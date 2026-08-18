"""Tokenizer + recursive-descent parser for the M subset the census needs.

Subset (per HANDOFF_SHAPE_CENSUS amendment 1): let/in, function
application, string concatenation (&), records, lists, navigation
(item/field access), identifiers and parameters, literals, if/each/try.
Anything beyond the subset degrades to an Opaque node — the parser NEVER
raises: total classification must not depend on total parsing.

Grammar reference: Microsoft's powerquery-parser. This is deliberately
the smallest AST that lets signatures capture argument KINDS
(literal vs parameter vs concatenation) — the discriminator the field
census proved necessary.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# --- AST -------------------------------------------------------------


@dataclass
class Lit:
    kind: str  # "string" | "number" | "logical" | "null"
    value: str = ""


@dataclass
class Ref:
    name: str
    quoted: bool = False  # #"quoted identifier"


@dataclass
class Call:
    func: "object"          # usually a Ref
    args: "list" = field(default_factory=list)

    @property
    def name(self) -> str:
        return self.func.name if isinstance(self.func, Ref) else ""


@dataclass
class Rec:
    fields: "list[tuple[str, object]]" = field(default_factory=list)


@dataclass
class Lst:
    items: "list" = field(default_factory=list)


@dataclass
class BinOp:
    op: str
    left: "object"
    right: "object"


@dataclass
class FieldAccess:
    base: "object"
    fieldname: str


@dataclass
class ItemAccess:
    base: "object"
    selector: "object"


@dataclass
class Let:
    bindings: "list[tuple[str, object]]"
    body: "object"


@dataclass
class Each:
    body: "object"


@dataclass
class If:
    cond: "object"
    then: "object"
    els: "object"


@dataclass
class Opaque:
    text: str = ""


# --- Tokenizer -------------------------------------------------------

_TOKEN_RE = re.compile(
    r"""
    (?P<ws>\s+|//[^\n]*|/\*.*?\*/)
  | (?P<string>"(?:[^"]|"")*")
  | (?P<qident>\#"(?:[^"]|"")*")
  | (?P<hashfn>\#[a-z]+)
  | (?P<number>0x[0-9A-Fa-f]+|\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)
  | (?P<ident>[A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)*)
  | (?P<arrow>=>)
  | (?P<cmp><>|<=|>=|\.\.\.|\.\.)
  | (?P<punct>[()\[\]{},=&@<>+\-*/;?.])
    """,
    re.VERBOSE | re.DOTALL,
)

KEYWORDS = {"let", "in", "each", "if", "then", "else", "true", "false",
            "null", "and", "or", "not", "try", "otherwise", "type", "as",
            "is", "meta", "error", "section", "shared"}

BINARY_OPS = {"&", "+", "-", "*", "/", "=", "<>", "<", ">", "<=", ">=",
              "and", "or", "??", "meta", "as", "is"}


def tokenize(text: str) -> "list[tuple[str, str]]":
    tokens: "list[tuple[str, str]]" = []
    pos = 0
    while pos < len(text):
        m = _TOKEN_RE.match(text, pos)
        if not m:
            tokens.append(("other", text[pos]))
            pos += 1
            continue
        pos = m.end()
        kind = m.lastgroup
        val = m.group()
        if kind == "ws":
            continue
        if kind == "string":
            tokens.append(("string", val[1:-1].replace('""', '"')))
        elif kind == "qident":
            tokens.append(("qident", val[2:-1].replace('""', '"')))
        elif kind == "ident" and val in KEYWORDS:
            tokens.append(("kw", val))
        else:
            tokens.append((kind, val))
    return tokens


# --- Parser ----------------------------------------------------------


class _Parser:
    def __init__(self, tokens: "list[tuple[str, str]]") -> None:
        self.toks = tokens
        self.i = 0

    def peek(self) -> "tuple[str, str]":
        return self.toks[self.i] if self.i < len(self.toks) else ("eof", "")

    def next(self) -> "tuple[str, str]":
        t = self.peek()
        self.i += 1
        return t

    def accept(self, kind: str, val: "str | None" = None) -> bool:
        k, v = self.peek()
        if k == kind and (val is None or v == val):
            self.i += 1
            return True
        return False

    def expect(self, kind: str, val: "str | None" = None) -> "tuple[str, str]":
        k, v = self.peek()
        if k != kind or (val is not None and v != val):
            raise SyntaxError(f"expected {kind} {val!r}, got {k} {v!r}")
        return self.next()

    def expression(self):
        k, v = self.peek()
        if (k, v) == ("kw", "let"):
            return self.let_expr()
        if (k, v) == ("kw", "if"):
            self.next()
            cond = self.expression()
            self.expect("kw", "then")
            then = self.expression()
            self.expect("kw", "else")
            els = self.expression()
            return If(cond, then, els)
        if (k, v) == ("kw", "each"):
            self.next()
            return Each(self.expression())
        if (k, v) == ("kw", "try"):
            self.next()
            expr = self.expression()
            if self.accept("kw", "otherwise"):
                fallback = self.expression()
                return BinOp("otherwise", expr, fallback)
            return expr
        if (k, v) == ("kw", "error"):
            self.next()
            return Opaque("error " + str(self.expression()))
        return self.binop_expr()

    def let_expr(self):
        self.expect("kw", "let")
        bindings: "list[tuple[str, object]]" = []
        while True:
            name = self.binding_name()
            self.expect("punct", "=")
            value = self.expression()
            bindings.append((name, value))
            if not self.accept("punct", ","):
                break
        self.expect("kw", "in")
        body = self.expression()
        return Let(bindings, body)

    def binding_name(self) -> str:
        k, v = self.next()
        if k in ("ident", "qident"):
            return v
        raise SyntaxError(f"expected binding name, got {k} {v!r}")

    def binop_expr(self):
        left = self.unary_expr()
        while True:
            k, v = self.peek()
            op = v if (k == "punct" and v in BINARY_OPS) else \
                v if (k == "cmp" and v in BINARY_OPS) else \
                v if (k == "kw" and v in BINARY_OPS) else None
            if op is None:
                return left
            self.next()
            # `x as type`, `x is type`, `x meta rec` — consume the right
            # side generically; the census only distinguishes `&`.
            right = self.unary_expr()
            left = BinOp(op, left, right)

    def unary_expr(self):
        k, v = self.peek()
        if k == "punct" and v in ("-", "+", "@"):
            self.next()
            return self.postfix_expr()  # sign/scoping is kind-neutral
        if (k, v) == ("kw", "not"):
            self.next()
            return self.postfix_expr()
        return self.postfix_expr()

    def postfix_expr(self):
        expr = self.primary()
        while True:
            k, v = self.peek()
            if (k, v) == ("punct", "("):
                self.next()
                args = []
                if not self.accept("punct", ")"):
                    while True:
                        args.append(self.expression())
                        if not self.accept("punct", ","):
                            break
                    self.expect("punct", ")")
                expr = Call(expr, args)
            elif (k, v) == ("punct", "{"):
                self.next()
                sel = self.expression()
                self.expect("punct", "}")
                expr = ItemAccess(expr, sel)
            elif (k, v) == ("punct", "["):
                # field access: [Name] — a record can't follow an
                # expression, so a single name + ] is an access
                self.next()
                fk, fv = self.peek()
                if fk in ("ident", "qident"):
                    save = self.i
                    self.next()
                    if self.accept("punct", "]"):
                        expr = FieldAccess(expr, fv)
                        continue
                    self.i = save
                raise SyntaxError("unsupported bracket form after expression")
            else:
                return expr

    def primary(self):
        k, v = self.next()
        if k == "string":
            return Lit("string", v)
        if k == "number":
            return Lit("number", v)
        if k == "kw" and v in ("true", "false"):
            return Lit("logical", v)
        if k == "kw" and v == "null":
            return Lit("null")
        if k in ("ident", "qident"):
            return Ref(v, quoted=(k == "qident"))
        if k == "hashfn":
            return Ref(v)
        if (k, v) == ("punct", "("):
            expr = self.expression()
            self.expect("punct", ")")
            return expr
        if (k, v) == ("punct", "["):
            fields: "list[tuple[str, object]]" = []
            if not self.accept("punct", "]"):
                while True:
                    fk, fv = self.next()
                    if fk not in ("ident", "qident"):
                        raise SyntaxError(f"bad record key {fk} {fv!r}")
                    self.expect("punct", "=")
                    fields.append((fv, self.expression()))
                    if not self.accept("punct", ","):
                        break
                self.expect("punct", "]")
            return Rec(fields)
        if (k, v) == ("punct", "{"):
            items = []
            if not self.accept("punct", "}"):
                while True:
                    items.append(self.expression())
                    if not self.accept("punct", ","):
                        break
                self.expect("punct", "}")
            return Lst(items)
        raise SyntaxError(f"unexpected token {k} {v!r}")


def parse_m(text: str) -> "object":
    """Parse an M expression. NEVER raises — anything the subset cannot
    express comes back as Opaque (census classifies it unknown)."""
    try:
        tokens = tokenize(text)
        if not tokens:
            return Opaque("")
        p = _Parser(tokens)
        expr = p.expression()
        # trailing garbage means we misread the shape — be honest
        if p.peek()[0] != "eof":
            return Opaque(text[:200])
        return expr
    except (SyntaxError, RecursionError, IndexError):
        return Opaque(text[:200])
