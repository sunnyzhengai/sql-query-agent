"""R16 — THE BUSINESS VOICE TIER + THE MEANING LADDER
(Grammar_Floor v2.16.0, Brief_Business_Voice, every ruling Sunny's
quoted words, 2026-09-20).

The scope description's ruled tier order: a BLESSED business
sentence > a gate-PASSED `proposed` row (status carried) > the
mechanical R14 floor. A row voices only while its basis_hash
matches the recomputed basis (the mechanical sentence + every
material text): the SQL changes OR a dictionary row changes ->
STALE, counted, the floor voices. The registry
(glossary/business_sentences.json) is INPUT DATA exactly like KG1
descriptions — the verbatim law reads it through the ONE door,
effective_sentence().

The proposer is the R5.b seat widened from a word to a sentence:
an INJECTED model, the double-run law, the candidate cache, the
seat-down law; `blessed` is a ruled status the machine may never
write nor overwrite (the field law). THE GATE is mechanical and
model-free, violations named:
  GATE-BV1 nothing dropped — the grain lead, every value literal
    (or its noted words), and the payload frame must witness in
    the candidate; a semantic absorption of a source is licensed
    by direction 2, never by silence about a condition.
  GATE-BV2 nothing invented — every content word traces to a
    material text, the mechanical sentence, or the FRAME
    vocabulary (the core-slot grammar words). Units nobody wrote
    and clinician knowledge with no source row die here.
"""
import hashlib
import json
import re
from typing import Dict, List, Tuple

REGISTRY = "business_sentences.json"
SAME_TREE = "SAME-TREE scope "

# the core-slot grammar vocabulary (population · conditions ·
# what's carried) — frame words are the sentence's skeleton, never
# its facts; facts must trace to materials
FRAME_WORDS = frozenset(
    "population membership row rows record records list selection "
    "selections carrying carried carries per one each every "
    "distinct matched kept".split())
STOP_WORDS = frozenset(
    "the a an and or of for to in on at with is are was were has "
    "have had that this those these it its their be by from as not "
    "no only s more other into over under between during "
    # B6 (Sunny "agree with your fix to class 1", 2026-09-21):
    # connective English is sentence skeleton, never a fact — his
    # first batch measured the defect ('where' alone killed 98
    # rows). Fact words never join this list.
    "where whose which when while being been also along about "
    "based together plus without within against among both "
    "either neither includes include included including "
    "contains contain containing specified indicating "
    "additional "
    # B6.b (the #AllMeds live find): temporal prepositions, the
    # membership verb R14 itself speaks, and the core slots' own
    # names are skeleton too
    "before after match matches matching condition conditions "
    "number toward towards "
    # spelled small numbers state the same count the digit does
    "two three four five six seven eight nine ten eleven twelve "
    "thirteen fourteen fifteen sixteen seventeen eighteen "
    "nineteen twenty".split())
_WORD = re.compile(r"[a-z0-9]+")
# literal: grammar — the payload frame's word family (B6.c)
_CARRY_FAMILY = ("carrying", "carries", "carried", "carry",
                 "membership")
# a quoted literal, optionally with its noted words — the witness
# pair: the business voice may speak either half
_WITNESS = re.compile(r"'([^']+)'(?:\s*\(noted\s+'([^']+)'\))?")
# B6.b (the #AllMeds live find, 2026-09-21): the R5.c
# owner-possessive apostrophe ("the record's taken time") is NOT a
# quote delimiter — folded away before witnesses are read, else
# the text BETWEEN two possessives pairs into a nonsense witness
# no sentence can contain
_POSSESSIVE = re.compile(r"(?<=\w)'s\b")


def witness_pairs(mech_sentence: str) -> List[Tuple[str, str]]:
    """The nothing-dropped witnesses of a mechanical sentence:
    (literal, noted) pairs; the business voice may speak either
    half. Possessive apostrophes are folded first."""
    return _WITNESS.findall(_POSSESSIVE.sub("s", mech_sentence or ""))


def scope_witness_texts(read, scope) -> List[str]:
    """B8.2 (Sunny "agreed. go.", 2026-09-21): witnesses come from
    the GRAPH's condition rows — every condition description in
    the scope's has_part subtree (its own conditions, its joins'
    ON conditions, composite children). Quote pairing is then
    local to ONE clause; cross-clause artifacts cannot manufacture
    witnesses."""
    kids: Dict[str, List[str]] = {}
    for e in read.edges("has_part"):
        kids.setdefault(e.from_id, []).append(e.to_id)
    conditions = {n.identity: n.properties.get("description", "")
                  for n in read.nodes("condition")}
    texts, frontier, seen = [], [scope.get("name_key") or ""], set()
    while frontier:
        cur = frontier.pop()
        if cur in seen:
            continue
        seen.add(cur)
        if cur in conditions:
            if conditions[cur].strip():
                texts.append(conditions[cur])
        frontier.extend(kids.get(cur, []))
    return sorted(texts)


# ---- the synonym ledger (B8.4): the LLM NOMINATES a mapping, a
# mechanical stem guard verifies it, the pair lands as DATA the
# gate consumes deterministically — never a model at voice time

SYNONYMS = "synonym_ledger.json"
_STEM_MIN = 4


def stem_guard(word: str, source_word: str) -> bool:
    """A nomination survives only when the two words visibly share
    a stem — 'administered'/'administration' do; a laundering leap
    like 'kilograms'/'weight' never can."""
    a, b = (word or "").lower(), (source_word or "").lower()
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n >= _STEM_MIN


def load_synonyms(glossary_dir) -> Dict[str, Dict]:
    f = glossary_dir / SYNONYMS
    if not f.is_file():
        return {}
    from aisql.graph import kg1_intake
    return kg1_intake.read_json(f)


def save_synonyms(glossary_dir, rows: Dict[str, Dict]) -> None:
    glossary_dir.mkdir(parents=True, exist_ok=True)
    (glossary_dir / SYNONYMS).write_text(
        json.dumps({k: rows[k] for k in sorted(rows)}, indent=1))


def _forms(w: str) -> set:
    """Deterministic inflection folding (B6 plurals + B9.2
    -ing/-ed) — no list, no model."""
    out = {w, w.rstrip("s"), w + "s", w + "es"}
    if w.endswith("ing") and len(w) > 5:
        out |= {w[:-3], w[:-3] + "e"}
    if w.endswith("ed") and len(w) > 4:
        out |= {w[:-2], w[:-1]}
    return out


def acronym_form_guard(token: str, phrase: str) -> bool:
    """B9.5's mechanical half — the acronym analogue of the stem
    guard: the token IS the phrase's word-initials, or an
    in-order subsequence of its single word. 'abx'/'antibiotics'
    fails (the x maps to nothing) and stays human."""
    t = (token or "").lower()
    words = _fold(phrase or "")
    if not t or not words:
        return False
    if t == "".join(w[0] for w in words):
        return True
    if len(words) == 1:
        it = iter(words[0])
        return all(c in it for c in t)
    return False


ACRONYM_LEDGER = "acronym_ledger.json"


def _load_ledger(glossary_dir) -> Dict[str, Dict]:
    f = glossary_dir / ACRONYM_LEDGER
    if not f.is_file():
        return {}
    from aisql.graph import kg1_intake
    return kg1_intake.read_json(f)


def _save_ledger(glossary_dir, rows: Dict[str, Dict]) -> None:
    (glossary_dir / ACRONYM_LEDGER).write_text(
        json.dumps({k: rows[k] for k in sorted(rows)}, indent=1))


def acronym_prompt(token: str) -> str:
    """Abstract only (prompt-examples-are-data law); 'abbreviate'
    is the seat contract's marker."""
    return (f"In a hospital SQL estate's data context, what phrase "
            f"does the token '{token}' abbreviate? Answer the "
            "phrase alone, or null if you cannot say.")


def load_acronym_expansions(glossary_dir) -> Dict[str, str]:
    """B8.b: blessed/matched acronym expansions ARE rung-0
    material (R16 names blessed vocabulary). {token: expansions
    joined} — only human-ruled (`blessed`) and dictionary-matched
    (`matched`) rows speak; guesses never do."""
    from aisql.flows import glossary as g
    f = glossary_dir / g.LEDGER
    if not f.is_file():
        return {}
    from aisql.graph import kg1_intake
    out = {}
    for token, row in kg1_intake.read_json(f).items():
        exps = [e for e in (row.get("expansions") or [])
                if (e or "").strip()]
        if not exps:
            continue
        if row.get("status") in ("blessed", "matched"):
            out[token.lower()] = "; ".join(exps)
        elif row.get("status") == "proposed" and all(
                acronym_form_guard(token, e) for e in exps):
            # B9.5: a seat-nominated, FORM-GUARDED expansion
            # serves at proposed — Sunny blesses or kills at
            # leisure, nothing waits
            out[token.lower()] = "; ".join(exps)
    return out


SYN_PROMPT_VERSION = "s2"


def synonym_worklist(killed: List[str],
                     syn_rows: Dict[str, Dict]) -> List[str]:
    """Which killed words earn a seat ask: unseen words, plus
    tombstones from an OLDER prompt version (one re-ask per
    version — no basis ever pays twice under one prompt)."""
    out = []
    for w in killed:
        row = syn_rows.get(w)
        if row is None:
            out.append(w)
        elif row.get("source_word") is None \
                and row.get("prompt_version") != SYN_PROMPT_VERSION:
            out.append(w)
    return out


def synonym_prompt(words: List[str],
                   vocabulary: List[str] = None) -> str:
    """Abstract instructions only (the prompt-examples-are-data
    law). The 'grammatical form' marker is the seat contract.
    Each seat call is STATELESS — the source vocabulary rides in
    the prompt (B8.b; the s1 prompt referenced context the call
    never had and every nomination came back null)."""
    lines = ["For each word below, name the single vocabulary "
             "word it is a grammatical form or direct inflection "
             "of. Answer a JSON object mapping each word to that "
             "vocabulary word, or to null when no such word "
             "exists.",
             "Words:"]
    lines += [f"- {w}" for w in sorted(words)]
    if vocabulary:
        lines.append("Vocabulary:")
        lines.append(", ".join(sorted(set(vocabulary))))
    return "\n".join(lines)


def _fold(text: str) -> List[str]:
    return _WORD.findall((text or "").lower().replace("_", " "))


def _token_set(text: str) -> set:
    return set(_fold(text))


# ---- materials: rung 0 for a scope — every touched table's and
# column's DICTIONARY ROW (the FL35 remedy) + child scope
# sentences (same-rung composition; strict layering ends here)

def _touched(scope) -> Tuple[set, set, set]:
    """Walk the scope's whole captured structure for resolves_to:
    4-part = column (its table joins too), 3-part = table,
    SAME-TREE = a sibling scope key."""
    cols, tbls, kids = set(), set(), set()

    def walk(d):
        if isinstance(d, dict):
            r = d.get("resolves_to")
            if isinstance(r, str):
                if r.startswith(SAME_TREE):
                    kids.add(r[len(SAME_TREE):])
                elif r.count("|") == 3:
                    cols.add(r)
                    tbls.add(r.rsplit("|", 1)[0])
                elif r.count("|") == 2:
                    tbls.add(r)
            for v in d.values():
                walk(v)
        elif isinstance(d, list):
            for v in d:
                walk(v)

    walk(scope)
    return cols, tbls, kids


def materials(read, tree, scope,
              acronyms: Dict[str, str] = None) -> Dict[str, str]:
    """{material id: its words} — the proposer's whole world and
    the gate's source set. Each entry carries the identifier's
    readable fold AND the vendor's description verbatim. B8.b:
    ruled acronym expansions join for every token the scope's
    touched names carry."""
    del tree  # the scope's own structure names everything it reads
    cols, tbls, kids = _touched(scope)
    tables = {n.identity: n.properties for n in read.nodes("table")}
    columns = {n.identity: n.properties for n in read.nodes("column")}
    scopes = {n.identity: n.properties for n in read.nodes("scope")}
    mats: Dict[str, str] = {}
    for t in sorted(tbls):
        p = tables.get(t, {})
        words = " ".join(_fold(t.rsplit("|", 1)[-1]))
        mats[f"table {t}"] = f"{words}. {p.get('description', '')}"
    for c in sorted(cols):
        p = columns.get(c, {})
        words = " ".join(_fold(c.rsplit("|", 1)[-1]))
        mats[f"column {c}"] = f"{words}. {p.get('description', '')}"
    for k in sorted(kids):
        p = scopes.get(k, {})
        words = " ".join(_fold(k.rsplit("::", 1)[-1]))
        mats[f"scope {k}"] = f"{words}. {p.get('description', '')}"
    # B9.1: the author's own output aliases are source words
    names = [str(pr.get("name") or "")
             for pr in (scope.get("projection") or [])
             if isinstance(pr, dict) and (pr.get("name")
                                          or "").strip()]
    if names:
        mats["outputs " + (scope.get("name_key") or "")] = \
            " ".join(names)
    if acronyms:
        touched_tokens = set()
        for ident in tbls | cols | kids \
                | {scope.get("name_key") or ""}:
            touched_tokens |= set(_fold(ident.rsplit("|", 1)[-1]
                                        .rsplit("::", 1)[-1]))
        # B10 (FL37): B9.1's output aliases are source words, so
        # their tokens carry acronyms too — [LOS Hours] can be a
        # scope's only clean 'los' (LosHours folds to one word)
        for n in names:
            touched_tokens |= set(_fold(n))
        for t in sorted(touched_tokens & set(acronyms)):
            mats[f"acronym {t}"] = f"{t}. {acronyms[t]}"
    return mats


# ---- the basis: what the sentence was composed FROM

def basis_hash(mech_sentence: str, mats: Dict[str, str]) -> str:
    payload = "\x00".join([mech_sentence or ""]
                          + [f"{k}\x01{mats[k]}" for k in sorted(mats)])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---- THE GATE (mechanical, no model, named violations)

_LABEL_ALNUM = re.compile(r"[A-Za-z0-9]{3}")
# literal: grammar — marks that disqualify a witness half (B8.b)
_NOISE_MARKS = ("=", "--", ";", "\n")


def _label_like(s: str) -> bool:
    """A witness half counts only when it reads as a LABEL: some
    real word, and none of the raw-SQL/changelog marks."""
    return bool(s) and bool(_LABEL_ALNUM.search(s)) \
        and not any(m in s for m in _NOISE_MARKS)


def check_sentence(candidate: str, mech_sentence: str,
                   mats: Dict[str, str],
                   witness_texts: List[str] = None,
                   synonyms: Dict[str, Dict] = None) -> List[str]:
    violations: List[str] = []
    cand = (candidate or "").strip()
    if not cand:
        return ["GATE-BV1: empty candidate"]
    cand_lower = cand.lower()
    cand_tokens = _fold(cand)
    allowed = _token_set(mech_sentence)
    for text in mats.values():
        allowed |= _token_set(text)
    # B8.b: the condition rows' own words are the FLOOR's ruled
    # voice — sourced by definition; a spliced clause never kills
    # itself
    for text in (witness_texts or []):
        allowed |= _token_set(text)
    # GATE-BV2 — nothing invented
    seen = set()
    for w in cand_tokens:
        if w in seen or w in STOP_WORDS or w in FRAME_WORDS:
            continue
        seen.add(w)
        forms = _forms(w)
        if not forms.isdisjoint(allowed):
            continue
        # B8.4: a guard-passed ledger pair whose source word is
        # locally present licenses the inflection — data, no model
        mapped = (synonyms or {}).get(w, {}).get("source_word")
        if mapped and mapped in allowed and stem_guard(w, mapped):
            continue
        violations.append(f"GATE-BV2: '{w}' traces to no "
                          "source row")
    # GATE-BV1 — nothing dropped. With witness_texts (the graph's
    # condition rows, B8.2) pairing is per clause and a MULTI-value
    # list requires no verbatim witness (B8.1, Sunny "compression
    # acceptable" — the full list stays one drill-down away);
    # without texts, the legacy whole-sentence scan stands.
    if witness_texts is not None:
        required = []
        for text in witness_texts:
            pairs = witness_pairs(text)
            if len(pairs) == 1:
                required.append(pairs[0])
    else:
        required = witness_pairs(mech_sentence)
    cand_expanded = set()
    for w in cand_tokens:
        cand_expanded |= _forms(w)

    def _spoken(half: str) -> bool:
        if not half:
            return False
        if half.lower() in cand_lower:
            return True
        # B9.3: a witness is CONTENT, not bytes — a paraphrase
        # carrying every content word (inflection-tolerant)
        # satisfies it
        toks = [t for t in _fold(half) if t not in STOP_WORDS]
        return bool(toks) and all(
            not _forms(t).isdisjoint(cand_expanded) for t in toks)

    emitted = set()
    for literal, noted in required:
        # B8.b — the noise waiver: raw-SQL echoes, dated changelog
        # comments, and symbol literals are drill-down material,
        # never business witnesses; a witness must have a
        # label-like half
        if not (_label_like(literal) or _label_like(noted)):
            continue
        if _spoken(literal) or _spoken(noted):
            continue
        want = f"'{literal}'" + (f" (noted '{noted}')" if noted
                                 else "")
        if want in emitted:  # B9.4: one violation per witness
            continue
        emitted.add(want)
        violations.append(f"GATE-BV1: missing witness {want}")
    mech_lower = f" {(mech_sentence or '').lower()} "
    if " per " in mech_lower and " per " not in f" {cand_lower} ":
        violations.append("GATE-BV1: the grain lead ('per …') is "
                          "missing")
    # B6.c (the #LacticAcid live find): any carry-family
    # inflection speaks the payload frame
    if "carrying" in mech_lower and not any(
            w in cand_lower for w in _CARRY_FAMILY):
        violations.append("GATE-BV1: the payload ('carrying …' or "
                          "the membership-list form) is missing")
    return violations


# ---- the registry (INPUT DATA; Sunny's ruling surface)

def load_rows(glossary_dir) -> Dict[str, Dict]:
    f = glossary_dir / REGISTRY
    if not f.is_file():
        return {}
    from aisql.graph import kg1_intake
    return kg1_intake.read_json(f)


def save_rows(glossary_dir, rows: Dict[str, Dict]) -> None:
    """Sorted, indented — Sunny flips status to 'blessed' by hand
    (the field law)."""
    glossary_dir.mkdir(parents=True, exist_ok=True)
    (glossary_dir / REGISTRY).write_text(
        json.dumps({k: rows[k] for k in sorted(rows)}, indent=1))


# ---- THE ONE DOOR (the verbatim law reads through here)

def effective_sentence(read, tree, scope,
                       rows: Dict[str, Dict],
                       synonyms: Dict[str, Dict] = None,
                       acronyms: Dict[str, str] = None
                       ) -> Tuple[str, str]:
    """(sentence, tier): tier in blessed · proposed · stale ·
    floor. A basis move is judged by THE GATE, not the hash alone
    (FL36, Sunny "approve re-anchor-when-gate-clean" 2026-09-21):
    the sentence still gate-clean against the NEW basis keeps
    voicing and its hash RE-ANCHORS in place (the caller persists,
    stamped re_anchored_at — counted, never silent); gate-dirty =
    STALE, the floor voices. Without this, every proposal wave
    staled its siblings' blessed rows and blessing never
    converged."""
    from aisql.flows import produce
    mech = produce.scope_sentence(read, tree, scope)
    row = rows.get(scope.get("name_key") or "")
    if not row or row.get("status") not in ("blessed", "proposed") \
            or not (row.get("sentence") or "").strip():
        return mech, "floor"
    fresh = basis_hash(mech, mats := materials(read, tree, scope,
                                               acronyms=acronyms))
    if row.get("basis_hash") != fresh:
        if check_sentence(row["sentence"], mech, mats,
                          witness_texts=scope_witness_texts(read,
                                                            scope),
                          synonyms=synonyms):
            return mech, "stale"  # the drift broke a word's source
        row["basis_hash"] = fresh  # re-anchor: the words still hold
    return row["sentence"], row["status"]


# ---- the proposer seat (R5.b widened; injected model only)

PROMPT_VERSION = "bv1"


def proposal_prompt(mech_sentence: str, mats: Dict[str, str]) -> str:
    """The seat's whole world. Abstract instructions only — a
    concrete example in a prompt gets copied into unrelated
    outputs (the ruled prompt-examples-are-data law)."""
    # literal: frame — the seat's instruction lines
    lines = [
        "Write ONE business sentence describing a SQL selection "
        "for a reader who knows the business but not SQL.",
        "Slots, in order: the population (who or what is in, and "
        "one row per what), the conditions (as facts about "
        "records, never filter syntax), what is carried (or that "
        "the selection is a membership list when it carries only "
        "its key).",
        "Every content word MUST come from the source materials "
        "below or the mechanical sentence. Do not add knowledge "
        "of your own: no units, no clinical vocabulary, no "
        "purpose talk that no material states.",
        "Prefer the materials' own nouns over table or column "
        "identifiers; absorb joins into what they mean when the "
        "materials license it.",
        "",
        "The mechanical sentence (the complete fact basis):",
        mech_sentence or "",
        "",
        "The source materials:",
    ]
    for k in sorted(mats):
        lines.append(f"- [{k}] {mats[k]}")
    lines.append("")
    lines.append("Answer with the sentence alone.")
    return "\n".join(lines)


def repair_prompt(base_prompt: str, candidate: str,
                  violations: List[str]) -> str:
    """B7's second chance: the gate's named violations ARE the
    repair instructions. Abstract, no examples (the ruled
    prompt-examples-are-data law)."""
    return (base_prompt
            + "\n\nYour previous sentence:\n" + candidate
            + "\n\nThe gate rejected it for these named "
              "violations:\n" + "\n".join(violations)
            + "\nRewrite the ONE sentence fixing every violation: "
              "use only words the materials or the mechanical "
              "sentence contain, and include every missing "
              "witness. Answer with the sentence alone.")


def propose_sentences(read, glossary_dir, seat, model: str,
                      prompt_version: str = PROMPT_VERSION,
                      run_at: str = "", cache_path=None
                      ) -> Dict[str, int]:
    """One batch, at Sunny's hand only (the paid-call law).
    SINGLE-RUN, GATE-FIRST (B4, Sunny "ok, agreed" 2026-09-21):
    one seat run -> the gate -> proposed/rejected; the double-run
    law stays R5.b's, for word-sized output. B6 (same day, "agree
    with your fix to class 1"): a `rejected` verdict is RE-JUDGED
    at every batch from its stored candidates — the gate is code
    and code changes; the re-judge spends nothing, and a sentence
    Sunny hand-edited on a rejected row re-judges the same way.
    B7 (same day, his "either propose to the llm to fix the error
    or propose to me"): a gate-rejected candidate earns ONE repair
    call carrying the named violations; still dirty -> the row
    stays rejected WITH sentence + violations for his hand,
    repair_spent so no basis ever pays twice. Machine rows only;
    `blessed` untouchable, stale or not; prior `disputed` rows
    (the retired verdict) re-land through the gate for free."""
    from aisql.lenses import decisions
    rows = load_rows(glossary_dir)
    syn_rows = load_synonyms(glossary_dir)
    acr = load_acronym_expansions(glossary_dir)
    ledger = _load_ledger(glossary_dir)
    asked_tokens: set = set()
    cache: Dict[str, List[str]] = {}
    if cache_path is not None and cache_path.is_file():
        cache = json.loads(cache_path.read_text())
    # literal: shape — the batch report, counted never silent
    counts = {"proposed": 0, "rejected": 0,
              "kept": 0, "blessed_kept": 0, "model_calls": 0,
              "cache_hits": 0, "seat_error": 0,
              "re_judged": 0, "repaired_ok": 0,
              "synonyms_added": 0, "spliced": 0,
              "acronyms_nominated": 0}

    def _save_cache():
        if cache_path is not None:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(cache))

    for _key, tree in sorted(read.trees().items()):
        for scope in decisions.named_scopes(tree):
            target = scope.get("name_key") or ""
            prior = rows.get(target)
            if prior and prior.get("status") == "blessed":
                counts["blessed_kept"] += 1  # ruled, untouchable
                continue
            from aisql.flows import produce
            mech = produce.scope_sentence(read, tree, scope)
            mats = materials(read, tree, scope, acronyms=acr)
            bhash = basis_hash(mech, mats)
            same_key = (prior is not None
                        and prior.get("basis_hash") == bhash
                        and prior.get("proposer", {})
                        .get("model") == model
                        and prior.get("proposer", {})
                        .get("prompt_version") == prompt_version)
            if same_key and prior.get("status") == "proposed":
                counts["kept"] += 1  # same basis, verdict stands
                continue
            ck = f"{target}|{bhash}|{model}|{prompt_version}"
            candidates = list(cache.get(ck, []))
            if candidates:
                counts["cache_hits"] += 1
            free_rejudge = bool(same_key
                                and prior.get("status") == "rejected")
            if free_rejudge and prior.get("sentence") \
                    and prior["sentence"] not in candidates:
                # Sunny's hand-edit re-judges first (B6)
                candidates.insert(0, prior["sentence"])
            base = proposal_prompt(mech, mats)
            if not candidates:
                try:
                    candidates = [" ".join(str(seat(base)).split())]
                except Exception:  # noqa: BLE001 — the seat-down
                    # law: one dead call never kills the batch
                    counts["seat_error"] += 1
                    continue
                counts["model_calls"] += 1
                cache[ck] = candidates
                _save_cache()  # every paid run survives a crash
            if free_rejudge:
                counts["re_judged"] += 1
            texts = scope_witness_texts(read, scope)

            def gate(c):
                return check_sentence(c, mech, mats,
                                      witness_texts=texts,
                                      synonyms=syn_rows)

            chosen, verdict_v, repaired, spliced = (None, None,
                                                    False, False)
            for c in candidates:
                verdict_v = gate(c)
                if not verdict_v:
                    chosen = c
                    break
            if chosen is None:
                # B8.4 — the synonym round: the seat NOMINATES a
                # source word per killed word; the stem guard +
                # local presence verify; survivors land in the
                # ledger as data and the gate re-runs, free after
                killed = [m.group(1) for v in verdict_v
                          if (m := re.match(
                              r"GATE-BV2: '([^']+)'", v))]
                novel = synonym_worklist(killed, syn_rows)
                if novel:
                    vocab = sorted(
                        {w for t in mats.values()
                         for w in _fold(t)
                         if w not in STOP_WORDS and len(w) > 2})
                    try:
                        raw = str(seat(synonym_prompt(
                            novel, vocabulary=vocab)))
                        counts["model_calls"] += 1
                        pairs = json.loads(
                            raw[raw.find("{"):raw.rfind("}") + 1])
                    except Exception:  # noqa: BLE001 — seat-down /
                        # unparseable: the round just yields nothing
                        counts["seat_error"] += 1
                        pairs = {}
                    local = _token_set(mech)
                    for t in mats.values():
                        local |= _token_set(t)
                    for w in novel:
                        src = pairs.get(w)
                        if (isinstance(src, str)
                                and stem_guard(w, src)
                                and src.lower() in local):
                            # literal: shape — a ledger pair
                            syn_rows[w] = {
                                "source_word": src.lower(),
                                "proposed_at": run_at,
                                "prompt_version":
                                    SYN_PROMPT_VERSION,
                                "model": model}
                            counts["synonyms_added"] += 1
                        else:
                            # the TOMBSTONE: nomination failed —
                            # recorded so no batch re-asks; Sunny
                            # may hand-fill source_word later
                            # literal: shape
                            syn_rows[w] = {
                                "source_word": None,
                                "proposed_at": run_at,
                                "prompt_version":
                                    SYN_PROMPT_VERSION,
                                "model": model}
                    save_synonyms(glossary_dir, syn_rows)
                    for c in candidates:
                        verdict_v = gate(c)
                        if not verdict_v:
                            chosen = c
                            break
            if chosen is None and verdict_v and any(
                    v.startswith("GATE-BV2") for v in verdict_v):
                # B9.5 — the acronym round: an unreviewed ledger
                # token the scope's names carry earns ONE expansion
                # nomination; the FORM GUARD verifies; the row
                # lands `proposed` in the ledger (its ruled home)
                cols_t, tbls_t, kids_t = _touched(scope)
                toks = set()
                for ident in tbls_t | cols_t | kids_t \
                        | {target}:
                    toks |= set(_fold(ident.rsplit("|", 1)[-1]
                                      .rsplit("::", 1)[-1]))
                landed = False
                for t in sorted(toks):
                    lrow = ledger.get(t)
                    if t in asked_tokens or lrow is None \
                            or lrow.get("status") != "unreviewed" \
                            or lrow.get("nomination_version") \
                            == prompt_version:
                        continue
                    asked_tokens.add(t)
                    try:
                        phrase = " ".join(
                            str(seat(acronym_prompt(t))).split())
                    except Exception:  # noqa: BLE001 — seat-down
                        counts["seat_error"] += 1
                        continue
                    counts["model_calls"] += 1
                    if phrase and phrase.lower() != "null" \
                            and acronym_form_guard(t, phrase):
                        # literal: shape — the nominated ledger row
                        ledger[t] = {**lrow, "status": "proposed",
                                     "expansions": [phrase],
                                     "proposed_at": run_at,
                                     "form_guard": True,
                                     # literal: shape
                                     "proposer": {
                                         "model": model,
                                         "seat": "sentence-batch"}}
                        counts["acronyms_nominated"] += 1
                        acr[t] = phrase
                        landed = True
                    else:
                        ledger[t] = {**lrow, "nomination_version":
                                     prompt_version}
                    _save_ledger(glossary_dir, ledger)
                if landed:
                    # the basis grew a material — recompute and
                    # re-judge, free
                    mats = materials(read, tree, scope,
                                     acronyms=acr)
                    bhash = basis_hash(mech, mats)
                    for c in candidates:
                        verdict_v = gate(c)
                        if not verdict_v:
                            chosen = c
                            break
            repair_spent = bool(same_key
                                and prior.get("repair_spent"))
            if chosen is None and not repair_spent:
                # B7: ONE repair, the violations in hand
                try:
                    fixed = " ".join(str(seat(repair_prompt(
                        base, candidates[-1], verdict_v))).split())
                except Exception:  # noqa: BLE001 — seat-down law;
                    # transient: retry allowed at the next batch
                    counts["seat_error"] += 1
                    fixed = None
                if fixed is not None:
                    counts["model_calls"] += 1
                    repair_spent = True
                    candidates.append(fixed)
                    cache[ck] = candidates
                    _save_cache()
                    verdict_v = gate(fixed)
                    if not verdict_v:
                        chosen, repaired = fixed, True
            if chosen is None and verdict_v \
                    and all(v.startswith("GATE-BV1") for v in
                            verdict_v):
                # B8.3 — the mechanical splice: the missing
                # condition's FLOOR CLAUSE is ruled text; append
                # it, re-gate, nothing waits on a person
                additions = []
                for v in verdict_v:
                    m = re.search(r"missing witness '([^']+)'", v)
                    if m:
                        lit = m.group(1)
                        clause = next((t for t in texts
                                       if lit in t), None)
                        if clause and clause not in additions:
                            additions.append(clause)
                    elif "payload" in v and "carrying" in \
                            mech.lower():
                        i = mech.lower().find("carrying")
                        additions.append(mech[i:].rstrip("."))
                if additions:
                    spliced_c = (candidates[-1].rstrip(". ")
                                 + "; also: "
                                 + "; ".join(a.rstrip(".")
                                             for a in additions)
                                 + ".")
                    if not gate(spliced_c):
                        chosen, spliced = spliced_c, True
                        counts["spliced"] += 1
            # literal: shape — the machine row; a human flips 'blessed'
            row = {"status": "", "basis_hash": bhash,
                   "proposed_at": run_at,
                   # literal: shape
                   "proposer": {"model": model,
                                "prompt_version": prompt_version,
                                "runs": len(candidates)}}
            if repair_spent:
                row["repair_spent"] = True
            if chosen is not None:
                row["status"] = "proposed"
                row["sentence"] = chosen
                if repaired:
                    row["repaired"] = True
                    counts["repaired_ok"] += 1
                if spliced:
                    row["spliced"] = True
                counts["proposed"] += 1
            else:
                row["status"] = "rejected"
                row["sentence"] = candidates[-1]
                row["violations"] = verdict_v
                counts["rejected"] += 1
            rows[target] = row
    save_rows(glossary_dir, rows)
    _save_cache()
    return counts
