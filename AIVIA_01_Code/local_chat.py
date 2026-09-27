# local_chat.py — PSEUDO CODE ONLY, awaiting Sunny's review.
# Real code will be written directly below these comments after approval.
#
# Design:   AIVIA_01_Design/01_subject_sql_files.md (the local web chat step)
# Contract: AIVIA_01_Design/01_subject_sql_files_data_contract.md
# Tests:    AIVIA_01_Test/test_01_local_chat.py (Claude's, written RED first)
#           AIVIA_01_Test/test_01_subject_sql_files_data_contract_sunny.md
#           (Sunny's hand cases — typed into this chat's page)
#
# Purpose: test the embeddings locally, before the Fabric move. Reads the
# data sheet json, embeds the user's question with the SAME model
# (text-embedding-3-large, real paid call), ranks ALL files by cosine
# similarity, returns every file name with its score — never a filtered
# subset, ranking is the answer.
#
# Two layers, so the logic is testable without the web page:
#
# LAYER 1 — pure functions (pytest tests these directly)
#
#   cosine_similarity(a, b)
#       Standard formula: dot(a, b) / (norm(a) * norm(b)).
#       Plain Python over the 3072 numbers — no new packages; the only
#       pinned packages are openai/pytest/ruff, and 8 files x 3072
#       numbers needs no numpy.
#
#   rank_files(question_embedding, rows)
#       For every row in the data sheet: score = cosine similarity of
#       the question embedding vs the row's file_name_embedding.
#       Return ALL rows as {file_name, score}, sorted by score,
#       highest first. No cutoff, no top-k.
#
#   answer(question, sheet_path, embedder)
#       Load the data sheet json. Embed the question — ONE call via the
#       passed-in embedder (same shape as the builder: names -> list of
#       embeddings). Return rank_files(...). This is the function the
#       tests pin and the web layer calls; it is also what the Fabric
#       chat step will reuse later with the graph as the row source.
#
# LAYER 2 — the web page (thin, no logic of its own)
#
#   Built on Python's standard library http.server — no flask/fastapi,
#   nothing new to pin.
#
#   GET  /      -> one self-contained HTML page: a question box, a Send
#                  button, and a results table (file name + score,
#                  highest first, all 8 rows, top row highlighted).
#   POST /ask   -> body {"question": "..."} -> embeds the question with
#                  the real OpenAI embedder (key read from .env at repo
#                  root, same as the tests read it) -> returns the
#                  ranked list as json for the page to render.
#
#   Startup (the command Sunny runs):
#       /opt/homebrew/bin/python3.11 AIVIA_01_Code/local_chat.py \
#           AIVIA_01_Data/01_subject_sql_files/01_subject_sql_files_data_sheet.json
#       The sheet path is a COMMAND-LINE PARAMETER — never written inside
#       the code, per the design doc's paths-are-parameters law.
#       Port 8701 by default, overridable as a second argument.
#       Prints the address (http://localhost:8701) so Sunny can click it.
#       Each question costs one paid embedding call; the 8 file
#       embeddings are read from the sheet, never re-embedded.
#
# CLAUDE'S TESTS (red first, in test_01_local_chat.py) — they pin:
#   - answer() returns ALL files, each with a numeric score, sorted
#     highest first
#   - cosine_similarity of a vector with itself = 1.0 (within rounding)
#   - Sunny's rankable hand cases, mechanically:
#       "Which reports for CCMC?" -> the two CCMC file names hold the
#       top 2 positions
#       "Which reports are for hospitalist census?" -> the Hospitalist
#       file name holds position 1
#     (The inpatient-census case stays Sunny's-eye-only — her md says
#     those three "may or may not" rank highest, so no test pins it.)
#   - real embedder throughout — no fake calls.
#
# After build, Claude updates Sunny's md with the exact commands: the
# pytest command (unchanged) plus the chat startup command above.

import json
import math
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

DEFAULT_PORT = 8701
EMBEDDING_MODEL = "text-embedding-3-large"


# --------------------------------------------------------------------------
# Layer 1 — pure functions
# --------------------------------------------------------------------------


def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b)


def rank_files(question_embedding, rows):
    scored = [
        {
            "file_name": row["file_name"],
            "score": cosine_similarity(question_embedding, row["file_name_embedding"]),
        }
        for row in rows
    ]
    return sorted(scored, key=lambda r: r["score"], reverse=True)


def answer(question, sheet_path, embedder):
    with open(sheet_path, encoding="utf-8") as f:
        rows = json.load(f)
    [question_embedding] = embedder([question])
    return rank_files(question_embedding, rows)


# --------------------------------------------------------------------------
# Layer 2 — the web page
# --------------------------------------------------------------------------


def load_openai_key():
    env_file = Path(__file__).resolve().parents[1] / ".env"
    if not env_file.exists():
        raise FileNotFoundError(
            f"No .env at {env_file} — the contract says the key lives there"
        )
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("OPENAI_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise ValueError(f"OPENAI_API_KEY not found in {env_file}")


def real_embedder(names):
    from openai import OpenAI

    client = OpenAI(api_key=load_openai_key())
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=list(names))
    return [item.embedding for item in response.data]


PAGE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>AIVIA_01 local chat — embedding test</title>
<style>
  body { font-family: -apple-system, sans-serif; max-width: 760px; margin: 2rem auto; }
  #question { width: 70%; padding: 0.5rem; font-size: 1rem; }
  button { padding: 0.5rem 1rem; font-size: 1rem; }
  table { border-collapse: collapse; margin-top: 1rem; width: 100%; }
  td, th { border: 1px solid #ccc; padding: 0.4rem 0.6rem; text-align: left; }
  tr.top { background: #e6f4e6; font-weight: bold; }
  #status { color: #666; margin-top: 0.5rem; }
</style>
</head>
<body>
<h2>AIVIA_01 local chat — embedding test</h2>
<p>Every question costs one paid embedding call (text-embedding-3-large).
All 8 files come back ranked, highest similarity first.</p>
<input id="question" placeholder="What reports are for census?">
<button onclick="ask()">Send</button>
<div id="status"></div>
<div id="results"></div>
<script>
async function ask() {
  const q = document.getElementById('question').value.trim();
  if (!q) return;
  document.getElementById('status').textContent = 'embedding the question…';
  const resp = await fetch('/ask', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({question: q})
  });
  if (!resp.ok) {
    document.getElementById('status').textContent = 'ERROR: ' + await resp.text();
    return;
  }
  const ranked = await resp.json();
  document.getElementById('status').textContent = '';
  let html = '<table><tr><th>#</th><th>file_name</th><th>score</th></tr>';
  ranked.forEach((r, i) => {
    html += `<tr class="${i === 0 ? 'top' : ''}"><td>${i + 1}</td>` +
            `<td>${r.file_name}</td><td>${r.score.toFixed(4)}</td></tr>`;
  });
  html += '</table>';
  document.getElementById('results').innerHTML = html;
}
document.getElementById('question').addEventListener('keydown',
  e => { if (e.key === 'Enter') ask(); });
</script>
</body>
</html>
"""


class ChatHandler(BaseHTTPRequestHandler):
    sheet_path = None  # set by main() before the server starts

    def _send(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != "/ask":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            question = json.loads(self.rfile.read(length))["question"]
            ranked = answer(question, self.sheet_path, real_embedder)
            self._send(200, json.dumps(ranked).encode("utf-8"), "application/json")
        except Exception as e:  # noqa: BLE001 — fail loudly INTO the page, not a dead server
            self._send(500, f"{type(e).__name__}: {e}".encode("utf-8"), "text/plain")


def main(argv):
    if len(argv) < 2:
        print(
            "usage: python3.11 AIVIA_01_Code/local_chat.py "
            "<path to data sheet json> [port]",
            file=sys.stderr,
        )
        return 2
    sheet_path = Path(argv[1])
    if not sheet_path.exists():
        print(f"data sheet not found: {sheet_path}", file=sys.stderr)
        return 2
    port = int(argv[2]) if len(argv) > 2 else DEFAULT_PORT
    ChatHandler.sheet_path = sheet_path
    server = HTTPServer(("127.0.0.1", port), ChatHandler)
    print(f"AIVIA_01 local chat: http://localhost:{port}")
    print(f"data sheet: {sheet_path}")
    print("Ctrl+C to stop")
    server.serve_forever()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
