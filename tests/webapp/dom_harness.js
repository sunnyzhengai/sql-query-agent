// RW-19 (TESTPLAN_0062 section D, the runtime leg): the headless
// battery is API-only and structurally blind to page JS — the
// no-match card crashed on a null addEventListener and every static
// gate passed. This harness executes the REAL page script against a
// minimal purpose-built DOM (no jsdom dependency: our markup is our
// own, a compact parser covers it) and renders every card variant;
// a throw or a missing expected listener fails the python test.
//
// Usage: node dom_harness.js <page_script.js>
// Prints one JSON verdict line: {ok, failures: [...]}.

'use strict';

// ---- minimal element model -------------------------------------------

let ID = 0;

class El {
  constructor(tag) {
    this.tagName = (tag || 'div').toUpperCase();
    this.children = [];
    this.parent = null;
    this.attrs = {};
    this.listeners = {};
    this.textContent = '';
    this.dataset = {};
    this.checked = false;
    this.disabled = false;
    this._id = ++ID;
  }
  get className() { return this.attrs['class'] || ''; }
  set className(v) { this.attrs['class'] = v; }
  get id() { return this.attrs['id'] || ''; }
  addEventListener(name, fn) {
    (this.listeners[name] = this.listeners[name] || []).push(fn);
  }
  appendChild(el) {
    el.parent = this;
    this.children.push(el);
    return el;
  }
  remove() {
    if (this.parent) {
      this.parent.children = this.parent.children.filter(
        c => c !== this);
      this.parent = null;
    }
  }
  replaceWith(el) {
    if (this.parent) {
      const i = this.parent.children.indexOf(this);
      el.parent = this.parent;
      this.parent.children[i] = el;
      this.parent = null;
    }
  }
  get firstElementChild() { return this.children[0] || null; }
  get innerHTML() {
    // only used by esc() on a childless span: return escaped text
    return String(this.textContent)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }
  set innerHTML(html) {
    this.children = parseHTML(html).map(c => { c.parent = this; return c; });
  }
  _all() {
    const out = [];
    const walk = (n) => { for (const c of n.children) { out.push(c); walk(c); } };
    walk(this);
    return out;
  }
  _matches(sel) {
    sel = sel.trim();
    const attr = sel.match(/^([a-z]+)?\[([a-z-]+)=([^\]]+)\]$/i);
    if (attr) {
      const [, tag, k, v] = attr;
      if (tag && this.tagName !== tag.toUpperCase()) return false;
      return (this.attrs[k] || '') === v.replace(/^['"]|['"]$/g, '');
    }
    if (sel.startsWith('.')) {
      return (' ' + this.className + ' ').includes(' ' + sel.slice(1) + ' ');
    }
    if (sel.startsWith('#')) return this.id === sel.slice(1);
    return this.tagName === sel.toUpperCase();
  }
  querySelector(sel) {
    return this._all().find(e => e._matches(sel)) || null;
  }
  querySelectorAll(sel) {
    return this._all().filter(e => e._matches(sel));
  }
  get scrollHeight() { return 0; }
  set scrollTop(_v) {}
  focus() {}
}

// ---- a compact parser for OUR markup (tags, attrs, text) -------------

const VOID = new Set(['input', 'br', 'img', 'hr']);

function parseHTML(html) {
  const root = new El('root');
  const stack = [root];
  const re = /<!--[\s\S]*?-->|<\/?[a-zA-Z][^>]*>|[^<]+/g;
  let m;
  while ((m = re.exec(html)) !== null) {
    const tok = m[0];
    if (tok.startsWith('<!--')) continue;
    if (tok[0] !== '<') {
      const top = stack[stack.length - 1];
      top.textContent += tok
        .replace(/&amp;/g, '&').replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>').replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'");
      continue;
    }
    if (tok[1] === '/') { stack.pop(); continue; }
    const tag = tok.match(/^<([a-zA-Z0-9]+)/)[1].toLowerCase();
    const el = new El(tag);
    const attrRe = /([a-zA-Z-]+)(?:="([^"]*)"|='([^']*)')?/g;
    let a;
    const body = tok.replace(/^<[a-zA-Z0-9]+/, '').replace(/\/?>$/, '');
    while ((a = attrRe.exec(body)) !== null) {
      const k = a[1];
      const v = a[2] !== undefined ? a[2] : (a[3] !== undefined ? a[3] : '');
      el.attrs[k] = v;
      if (k.startsWith('data-')) {
        el.dataset[k.slice(5).replace(/-([a-z])/g,
          (_x, c) => c.toUpperCase())] = v;
      }
      if (k === 'checked') el.checked = true;
    }
    stack[stack.length - 1].appendChild(el);
    if (!VOID.has(tag) && !tok.endsWith('/>')) stack.push(el);
  }
  return root.children.map(c => { c.parent = null; return c; });
}

// ---- document / environment stubs ------------------------------------

const byId = {};
for (const id of ['log', 'q', 'askbtn', 'ask', 'graphpanel',
                  'persona', 'inbox', 'inboxnote']) {
  byId[id] = new El(id === 'ask' ? 'form' : 'div');
  byId[id].attrs['id'] = id;
  byId[id].value = '';
}
// GRAPH-PANEL-1: the shape panel's slots exist like on the page
byId['graphpanel'].innerHTML =
  '<div class="gp-svg"></div><div class="gp-card"></div>';
byId['graphpanel'].style = {};

global.document = {
  createElement: (t) => new El(t),
  getElementById: (id) => byId[id] || null,
};
global.window = global;
global.fetch = () => new Promise(() => {});   // never resolves — sync render only
global.EventSource = function () {};
global.TextDecoder = function () { this.decode = () => ''; };
// node 21+ ships a real global navigator (getter-only) — fine as-is

// ---- load the page script --------------------------------------------

const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
const failures = [];
try {
  // eslint-disable-next-line no-eval
  (0, eval)(src);
} catch (e) {
  failures.push('page script top-level threw: ' + e.message);
  console.log(JSON.stringify({ ok: false, failures }));
  process.exit(0);
}

function check(name, fn) {
  try { fn(); } catch (e) {
    failures.push(name + ': ' + (e && e.message));
  }
}

function expectListeners(card, sel, want, name) {
  const el2 = card.querySelector(sel);
  if (want && (!el2 || !(el2.listeners['click'] || []).length)) {
    failures.push(name + ': expected a wired ' + sel);
  }
  if (!want && el2) {
    failures.push(name + ': ' + sel + ' should not exist');
  }
}

// ---- console-page mode (CONSOLE-2b red-first) ------------------------

const MODE = process.argv[3] || 'workbench';

function textOf(node) {
  let out = node.textContent || '';
  for (const c of node.children) out += ' ' + textOf(c);
  return out;
}

if (MODE === 'console') {
  check('console evidence renders the FULL composer card '
      + '(red-first: a payload-ignoring renderer fails)', () => {
    const node = renderEvidence({
      verdict: 'DIFFERS',
      set_summary: '80 value(s) shared · E11.80 only in CodesetB',
      contrast: 'reporting — DX_CODE IN (80 values); '
        + 'reports — DX_CODE IN (81 values)',
      fingerprints: [
        { id: 'a', name: 'Diabetic Codeset', owner: 'reporting',
          reads: ['DIAGNOSIS_CODES'],
          criterion: 'DX_CODE IN (80 values)',
          description: 'the hand-maintained list' }],
      diff_label: 'receipt: − a · + b',
      diff_lines: ['+ E11.80 — present only in one definition'],
    }, '2 hash groups');
    const text = textOf(node);
    for (const want of ['80 value(s) shared',
                        'DX_CODE IN (80 values)',
                        'Diabetic Codeset', 'DIAGNOSIS_CODES',
                        'receipt: − a · + b',
                        'the hand-maintained list']) {
      if (!text.includes(want)) {
        throw new Error('payload field not rendered: ' + want);
      }
    }
  });
  console.log(JSON.stringify({ ok: failures.length === 0,
                               failures }));
  process.exit(0);
}

// ---- every card variant renders and wires ----------------------------

check('understanding card', () => {
  const card = renderParseCard({
    parse_confirm: 'reading your question as: x',
    show: [{ entity: 'E', matches: [
      { id: 'id1', kind: 'step', name: 'N1' },
      { id: 'id2', kind: 'step', name: 'N2' }] }],
  }, 'q1');
  expectListeners(card, '.confirmparse', true, 'understanding card');
  expectListeners(card, '.doorbtn', true, 'understanding card');
  expectListeners(card, '.skipparse', true, 'understanding card');
});

check('no-match card (RW-19, the crash variant)', () => {
  const card = renderParseCard({
    parse_confirm: 'no catalog match', no_match: true, show: [],
  }, 'q2');
  expectListeners(card, '.confirmparse', false, 'no-match card');
  expectListeners(card, '.doorbtn', true, 'no-match card');
  expectListeners(card, '.skipparse', true, 'no-match card');
});

check('card skeleton + grounded fill', () => {
  handleStreamEvent('card', { parse_line: 'reading…', entities: ['a', 'b'] });
  handleStreamEvent('card', { grounded: { entity: 'a', matches:
    [{ id: 'i', kind: 'step', name: 'M' }] } });
  clearStage();
});

const conclusionVariants = {
  flags: { kind: 'flags', closing: 'c', cards: [{ identity: 'I',
    flag_class: 'misnomer', severity: 'INFO', member_count: 2,
    distinct_logics: 2, disposition: 'open', member_names: ['a', 'b'],
    why: 'w' }] },
  compare: { kind: 'compare', verdict: 'DIFFERS', verdict_note: 'n',
    contrast: 'reporting — DX; reports — MED',
    fingerprints: [{ id: 'a', name: 'A', owner: 'reporting',
      reads: ['T1'], criterion: 'X > 1', description: 'why A' }],
    diff_label: 'receipt: − a · + b',
    diff_lines: ['+ x', '- y'], items: [{ name: 'A', description: 'd' }] },
  definition: { kind: 'definition', name: 'N', description: 'D',
    criteria: 'c', flags_line: '' },
  policy_refusal: { kind: 'policy_refusal', refusal: 'R',
    definition: { name: 'N', description: 'D' } },
  lineage: { kind: 'lineage', grain_line: 'g', note: 'n' },
  feeds: { kind: 'feeds', name: 'Dash', executes_metrics: ['M1'],
    reads_tables: ['T1'], measures: [], link_state: '' },
  map: { kind: 'map', items: [{ name: 'A', record_kind: 'step',
    of_metric: 'm', description: 'd', steps: ['s'],
    source_tables: ['t'] }] },
  census: { kind: 'census', count_line: '30 metric(s)', total: 30,
    ref: 'R1', items: [{ name: 'M1', description: 'd1' }] },
};
for (const [name, c] of Object.entries(conclusionVariants)) {
  check('conclusion ' + name, () => {
    const node = renderConclusion({ conclusion: c, caption: '',
      caption_inputs: [], answered: true });
    if (!node) throw new Error('rendered null');
  });
}
check('conclusion none (prose only)', () => {
  renderConclusion({ conclusion: null, caption: 'plain answer',
    caption_inputs: [], answered: false });
});

check('output error fold', () => {
  renderOutput({ component: { op: 'compare', params: {} },
    error: 'guard engaged detail' });
});
check('subgraph panel renders and wires (GRAPH-PANEL-1)', () => {
  const box = renderSubgraph({
    nodes: [
      { id: 'm1', kind: 'metric', name: 'Active Diabetics',
        anchor: true },
      { id: 'transform:m1:Reg', kind: 'step', name: 'Reg' },
      { id: 'cluster:x', kind: 'flag', name: 'Misnomer',
        flag_class: 'misnomer' }],
    edges: [
      { from: 'm1', to: 'transform:m1:Reg', label: 'step',
        derived: false },
      { from: 'm1', to: 'cluster:x', label: 'compared',
        derived: true }],
    truncated: false,
  }, { step_id: 'transform:m1:Reg', rung: 2 });
  if (!box) throw new Error('panel did not render');
  const nodesDrawn = box.querySelectorAll('.gp-node');
  if (nodesDrawn.length !== 3) {
    throw new Error('expected 3 nodes, got ' + nodesDrawn.length);
  }
  for (const n of nodesDrawn) {
    if (!(n.listeners['click'] || []).length) {
      throw new Error('node not click-wired');
    }
  }
});

check('subgraph empty hides the panel', () => {
  const r = renderSubgraph(null, null);
  if (r !== null) throw new Error('expected null');
});

check('output result with run button row', () => {
  renderOutput({ component: { op: 'retrieve', params: {},
    auto_round: 1 }, result: { ref: 'R1', op: 'retrieve',
    params: {}, complete: true, universe: 'u', note: '',
    headline: 'h', rows: [{ id: 'transform:m:S', kind: 'step',
    name: 'S', sql_fragment: 'SELECT 1' }], count: 1 } });
});

console.log(JSON.stringify({ ok: failures.length === 0, failures }));
