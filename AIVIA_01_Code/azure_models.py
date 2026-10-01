# azure_models.py — PSEUDO CODE ONLY, awaiting Sunny's review.
# Real code will be written directly below these comments after approval.
#
# Design:   AIVIA_01_Design/04_fabric_move.md (M05, decision 4 — customer
#           Azure OpenAI at launch; THE PARITY LAW)
# Contract: AIVIA_01_Design/04_fabric_move_data_contract.md (models in
#           production; the runbook Step G facts, filled 2026-10-01)
# Tests:    AIVIA_01_Test/test_04_fabric_move_data_contract.py (grows an
#           M05 section, RED first)
#
# PURPOSE. The chat's model calls move to Sunny's Azure OpenAI — the
# launch posture. Same models, different door; the asset source
# (--fabric) and the model provider (--azure) are ORTHOGONAL
# parameters, so --fabric --azure together is the full production
# shape: data from the lakehouse, brains from Azure, keys governed.
#
# ---------------------------------------------------------------------
# THE PINNED FACTS (Step G, 2026-10-01 — constants here, named in the
# 04 contract):
#   AZURE_ENDPOINT      = "https://aivia.openai.azure.com/"
#   EMBED_DEPLOYMENT    = "text-embedding-3-large"   (the parity law:
#                         exactly the model that embedded the sheets)
#   CHAT_DEPLOYMENT     = "gpt-5-mini"
#   AZURE_API_VERSION   = one pinned api-version string (adjusted once
#                         at the live run if Azure rejects it, then
#                         frozen)
#   KEY VAULT           = aivia01-kv / aivia01-azure-openai-key — the
#                         PRODUCTION home, recorded in the contracts
#                         (closes the 02/03/04 TBDs). The production
#                         vault READER arrives with stage B's host;
#                         local development reads AZURE_OPENAI_KEY from
#                         .env (same law as OPENAI_API_KEY).
#
# ---------------------------------------------------------------------
# THE FUNCTIONS (mirror the OpenAI pair, one door each):
#   load_azure_key(env_path=repo .env) — reads AZURE_OPENAI_KEY; loud
#       if absent (names the file and the line to add).
#   azure_embedder(texts)  — AzureOpenAI client (the same pinned openai
#       package speaks Azure), EMBED_DEPLOYMENT, returns vectors; the
#       drop-in twin of local_chat.real_embedder.
#   azure_chat(system, user) — CHAT_DEPLOYMENT, json response format;
#       the drop-in twin of chat_bot.real_chat.
#
# ---------------------------------------------------------------------
# THE CHAT GAINS --azure (parameter, never a fork):
#   chat_bot.main: ChatBotHandler gains embedder/chat_llm attributes
#   (today hardcoded to the OpenAI pair — a two-line refactor); --azure
#   sets the Azure pair. The census prints the provider:
#       models: openai | azure (aivia.openai.azure.com)
#   Flags compose: --fabric --azure = production shape on port 8703.
#
# ---------------------------------------------------------------------
# THE PARITY CHECK (the law, mechanized — and kept as a STANDING test):
#   parity_check(dir02): load ONE known stored vector (PATIENT's
#       table_name_embedding from the table sheet — the small file),
#       re-embed the same text ("PATIENT") on EMBED_DEPLOYMENT, cosine
#       the two. PASS at >= 0.999 (same model, same version — expect
#       ~1.0); the verbatim number prints and lands in the design doc.
#       FAIL = STOP: the Azure deployment is not the stored model;
#       switching providers would corrupt search until everything
#       re-embeds. The CLI (Sunny's hand, recorded):
#           /opt/homebrew/bin/python3.11 AIVIA_01_Code/azure_models.py \
#               --parity AIVIA_01_Data/02_emr_data_dictionary
#
# ---------------------------------------------------------------------
# CLAUDE'S TESTS (M05 section of test_04, red first; Azure calls are
# REAL and cost pennies — the paid-call law):
#   - the constants pin the G4 facts verbatim (endpoint, deployments,
#     vault + secret names).
#   - load_azure_key: reads the line from an injected env file; absent
#     -> loud error naming AZURE_OPENAI_KEY.
#   - THE LIVE PARITY TEST: azure_embedder(["PATIENT"]) vs the stored
#     vector, cosine >= 0.999 — the parity law becomes a standing
#     regression test; if the Azure deployment ever drifts from the
#     stored model, the suite goes red.
#   - azure_chat mechanism-level: one real segmentation call returns
#     valid structure (the gpt-5-mini-on-Azure twin of the existing
#     segmentation test).
#   - --azure --fabric compose: the CLI accepts both (parse-level).
#
# After build: contracts close their secret-name TBDs (02/03/04) +
# the 04 contract pins endpoint/deployments; CLAUDE.md ops facts gain
# the AZURE_OPENAI_KEY line; the runbook gains Step H (the production-
# shape startup command + the parity run).

import json
import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent

# The Step G facts (2026-10-01), pinned — named in the 04 contract.
AZURE_ENDPOINT = "https://aivia.openai.azure.com/"
EMBED_DEPLOYMENT = "text-embedding-3-large"
CHAT_DEPLOYMENT = "gpt-5.4-mini"  # ADOPTED 2026-10-01: newer than the
#   planned gpt-5-mini, already deployed on aivia; chat has no parity law
AZURE_API_VERSION = "2024-10-21"  # adjusted ONCE at the first live
#                                   call if Azure rejects it, then frozen
KEY_VAULT_NAME = "aivia01-kv"          # the PRODUCTION key home;
KEY_VAULT_SECRET = "aivia01-azure-openai-key"  # reader arrives at stage B
PARITY_FLOOR = 0.999


def load_azure_key(env_path=None):
    env_path = Path(env_path) if env_path else CODE_DIR.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("AZURE_OPENAI_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise ValueError(
        f"AZURE_OPENAI_KEY not found in {env_path} — add the line "
        "AZURE_OPENAI_KEY=<the key> (the vault holds the production "
        f"copy: {KEY_VAULT_NAME}/{KEY_VAULT_SECRET})")


def _client():
    from openai import AzureOpenAI

    return AzureOpenAI(api_key=load_azure_key(),
                       azure_endpoint=AZURE_ENDPOINT,
                       api_version=AZURE_API_VERSION)


def azure_embedder(texts):
    """The drop-in twin of local_chat.real_embedder."""
    response = _client().embeddings.create(model=EMBED_DEPLOYMENT,
                                           input=list(texts))
    return [item.embedding for item in response.data]


def azure_chat(system, user):
    """The drop-in twin of chat_bot.real_chat."""
    response = _client().chat.completions.create(
        model=CHAT_DEPLOYMENT,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}])
    return json.loads(response.choices[0].message.content)


def parity_check(dir02):
    """THE PARITY LAW, mechanized: the Azure deployment must be the
    exact model that embedded the sheets. Verbatim cosine printed;
    the result lands in the design doc by Sunny's hand."""
    from local_chat import cosine_similarity

    sheet = json.loads(
        (Path(dir02) / "02_emr_data_dictionary_extraction_table.json")
        .read_text(encoding="utf-8"))
    patient = next(r for r in sheet if r["table_name"] == "PATIENT")
    [vector] = azure_embedder(["PATIENT"])
    cosine = cosine_similarity(vector, patient["table_name_embedding"])
    verdict = "PASS" if cosine >= PARITY_FLOOR else "FAIL"
    print(f"parity check: stored PATIENT vector vs {EMBED_DEPLOYMENT} "
          f"on {AZURE_ENDPOINT}")
    print(f"  cosine = {cosine:.6f}  (floor {PARITY_FLOOR})  -> {verdict}")
    if verdict == "FAIL":
        print("  STOP: the deployment is NOT the stored model — "
              "switching providers would corrupt search until "
              "everything re-embeds.")
    return cosine


def main(argv):
    if len(argv) >= 3 and argv[1] == "--parity":
        cosine = parity_check(argv[2])
        return 0 if cosine >= PARITY_FLOOR else 1
    print("usage: python3.11 AIVIA_01_Code/azure_models.py "
          "--parity <02 sheets dir>", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
