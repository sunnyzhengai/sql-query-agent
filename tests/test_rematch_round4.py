"""L0 tests for the Round-4 runner's fact accounting and scorecard writer.

Added after the Round-4 record audit (REVIEW_ROUND4_RECORD_AUDIT.md):
the hand-written miss characterization contradicted the machine table,
and the writer shipped untested. The rule these tests encode: scorecard
prose annotates machine-emitted lines, never free-writes a miss list.
"""

from devtools.rematch_round4 import (
    RAW_LOG,
    characterize,
    grade_fabric,
    scorecard_lines,
)

# --- characterize: overlap path (small name-set oracles) ---------------

READERS_ORACLE = {
    "required_any": [[
        "Sepsis Bundle Compliance Metrics",
        "Sepsis Bundle Compliance by Shift",
        "Sepsis Case Details",
        "Sepsis Case Encounters",
        "Sepsis Screening Tool Results",
    ]],
    "required_overlap": 2,
    "forbidden": [],
}


def test_overlap_path_counts_hits_and_missed():
    answer = ("The readers are Sepsis Case Encounters and "
              "Sepsis Screening Tool Results.")
    facts = characterize(answer, READERS_ORACLE)
    assert facts["need"] == 2
    assert facts["total"] == 5
    assert facts["hits"] == 2
    assert facts["hit"] == ["Sepsis Case Encounters",
                            "Sepsis Screening Tool Results"]
    assert facts["missed"] == ["Sepsis Bundle Compliance Metrics",
                               "Sepsis Bundle Compliance by Shift",
                               "Sepsis Case Details"]


def test_overlap_path_is_case_insensitive():
    facts = characterize("it reads sepsis case details.", READERS_ORACLE)
    assert facts["hit"] == ["Sepsis Case Details"]
    assert facts["hits"] == 1


def test_empty_answer_hits_nothing():
    facts = characterize("", READERS_ORACLE)
    assert facts["hits"] == 0
    assert facts["hit"] == []
    assert facts["missed"] == READERS_ORACLE["required_any"][0]


# --- characterize: group path (one hit needed per group) ---------------

GROUP_ORACLE = {
    "required_any": [["28"], ["metric", "metrics"]],
    "forbidden": ["27", "29"],
}


def test_group_path_one_alt_satisfies_each_group():
    facts = characterize("There are 28 metrics in the catalog.",
                         GROUP_ORACLE)
    assert facts["need"] == 2 and facts["total"] == 2
    assert facts["hits"] == 2
    assert facts["missed"] == []


def test_group_path_missed_group_reports_its_first_alt():
    facts = characterize("The catalog holds 28 entries.", GROUP_ORACLE)
    assert facts["hits"] == 1
    assert facts["missed"] == ["metric"]


# --- grade_fabric rides on characterize --------------------------------

def test_grade_fabric_pass_carries_facts_dict():
    g = grade_fabric("28 metrics", GROUP_ORACLE, {})
    assert g["facts_present"] is True
    assert g["dishonest"] is False
    assert g["fact_hits"] == 2
    assert g["facts"]["missed"] == []


def test_grade_fabric_forbidden_claim_is_dishonest():
    g = grade_fabric("There are 27 metrics", GROUP_ORACLE, {})
    assert g["facts_present"] is False
    assert g["dishonest"] is True


# --- scorecard writer: machine-emitted miss / partial-pass lines -------

def _row(family, question, home_facts, fabric_facts, fabric_present,
         home_present=True):
    return {
        "family": family, "question": question,
        "home": {"facts_present": home_present, "dishonest": False},
        "home_s": 1.0, "home_facts": home_facts,
        "fabric": {"facts_present": fabric_present, "dishonest": False,
                   "fact_hits": fabric_facts["hits"],
                   "facts": fabric_facts},
        "fabric_s": 2.0,
        "home_answer": "home text", "fabric_answer": "fabric text",
    }


FULL = {"need": 2, "hits": 5, "total": 5,
        "hit": ["a", "b", "c", "d", "e"], "missed": []}
PARTIAL = {"need": 2, "hits": 2, "total": 5,
           "hit": ["Sepsis Case Encounters", "Sepsis Shift Compliance"],
           "missed": ["Sepsis Case Details", "x", "y"]}
NONE_HIT = {"need": 2, "hits": 0, "total": 2, "hit": [],
            "missed": ["Sepsis Case Details", "Sepsis Case Encounters"]}


def test_writer_emits_partial_pass_and_miss_lines():
    rows = [
        _row("lineage", "which metrics use IP_SEPSIS", FULL, PARTIAL,
             fabric_present=True),
        _row("bridge", "how is Sepsis Case defined", FULL, NONE_HIT,
             fabric_present=False),
    ]
    text = "\n".join(scorecard_lines(rows, 1.0, 2.0))
    assert "## Misses and partial passes (machine-emitted)" in text
    assert ('- fabric PASS on partial overlap — lineage — '
            '"which metrics use IP_SEPSIS": hits 2/2 needed of 5') in text
    assert ('- fabric miss — bridge — "how is Sepsis Case defined": '
            'hits 0/2 needed of 2') in text
    # carried/absent name lists travel with every emitted line
    assert "carried: [Sepsis Case Encounters, Sepsis Shift Compliance]" in text
    assert "absent: [Sepsis Case Details, x, y]" in text


def test_writer_silent_on_full_hit_pass():
    rows = [_row("census", "how many metrics", FULL, FULL,
                 fabric_present=True)]
    text = "\n".join(scorecard_lines(rows, 1.0, 2.0))
    assert "PASS on partial overlap" not in text
    assert "miss —" not in text


def test_writer_header_points_at_raw_log():
    rows = [_row("census", "how many metrics", FULL, FULL,
                 fabric_present=True)]
    text = "\n".join(scorecard_lines(rows, 1.0, 2.0))
    assert RAW_LOG.name in text
    # the table row itself renders both surfaces and the verdict column
    assert "| census | PASS | 1.0 | PASS | 2.0 | homegrown |" in text
