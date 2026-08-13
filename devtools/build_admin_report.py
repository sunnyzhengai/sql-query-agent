"""Generate + deploy the AIVIA admin telemetry report (PBIR-Legacy).

Also injects the health MEASURES into the semantic model's TMDL
(updateDefinition), so the funnel/verdict visuals ship with every
customer's model — the installer runs both halves.

Authors the report definition programmatically — four pages of visuals
bound to the aivia_admin_telemetry Direct Lake model — and creates it
via the Fabric reports API. No hand-built visuals: this script IS the
phase-3 installer step in embryo (per-customer deployment = same parts,
different model id).

Run:  python3 devtools/build_admin_report.py --workspace <ws-id> \
          --model <semantic-model-id> [--name aivia_admin_telemetry_report]
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import time

import requests

FABRIC = "https://api.fabric.microsoft.com/v1"

# --- measures injected into the model (page 1's vocabulary) ------------

VALIDATION_STEPS = ["step1_loaded", "step2_parsed", "step3_canonical",
                    "step4_transforms", "step5_edges", "step6_traversal"]
STEP_LABELS = ["1 Loaded", "2 Parsed", "3 Canonical", "4 Transforms",
               "5 Edges", "6 Traversable"]

MODEL_MEASURES = {
    "ops_pipeline_validation": [
        ("Metrics Total", "COUNTROWS(ops_pipeline_validation)", "0"),
        *[(f"Passed {label}",
           f"CALCULATE(COUNTROWS(ops_pipeline_validation), "
           f"ops_pipeline_validation[{col}] = TRUE())", "0")
          for col, label in zip(VALIDATION_STEPS, STEP_LABELS)],
        ("Metrics Fully Valid",
         "[Passed 6 Traversable] & \" / \" & [Metrics Total]", None),
    ],
    "ops_build_summary": [
        ("Last Build", "MAX(ops_build_summary[build_time])", None),
    ],
    "output_metric_logic": [
        ("Certified Metrics", "COUNTROWS(output_metric_logic)", "0"),
        ("Total Calculation Steps",
         "SUM(output_metric_logic[transform_count])", "0"),
        *[(f"Pct With {label}",
           f"DIVIDE(CALCULATE(COUNTROWS(output_metric_logic), "
           f"output_metric_logic[{col}] <> \"\"), "
           f"COUNTROWS(output_metric_logic))", "0%")
          for col, label in [("description", "Description"),
                             ("business_name", "Business Name"),
                             ("steward", "Steward"),
                             ("developer", "Developer"),
                             ("report_url", "Report Link")]],
        ("Missing Steward",
         "COUNTROWS(output_metric_logic) - CALCULATE("
         "COUNTROWS(output_metric_logic), "
         "output_metric_logic[steward] <> \"\")", "0"),
    ],
    "ops_parse_results": [
        ("Objects Parsed", "COUNTROWS(ops_parse_results)", "0"),
    ],
    "gov_turn_events": [
        ("Turns", "COUNTROWS(gov_turn_events)", "0"),
        ("Distinct Users", "DISTINCTCOUNT(gov_turn_events[user_id])", "0"),
        *[(label,
           f"CALCULATE(COUNTROWS(gov_turn_events), "
           f"gov_turn_events[{col}] = TRUE())", "0")
          for col, label in [("verified_by_tool", "Verified By Tool"),
                             ("llm_assembled", "LLM Assembled"),
                             ("search_only", "Search Only"),
                             ("no_tools", "No Tools"),
                             ("unverified_sameness_language",
                              "Unverified Sameness Claims")]],
        ("Tool Errors", "SUM(gov_turn_events[tool_errors]) + 0", "0"),
    ],
    "gov_feedback_events": [
        ("Feedback Events", "COUNTROWS(gov_feedback_events)", "0"),
        ("Not Helpful",
         "CALCULATE(COUNTROWS(gov_feedback_events), "
         "gov_feedback_events[verdict] = \"not_helpful\") + 0", "0"),
    ],
    "ops_installation_errors": [
        ("Errors On Record", "COUNTROWS(ops_installation_errors) + 0", "0"),
    ],
}


def measures_tmdl(table: str) -> str:
    import uuid
    out = []
    for name, dax, fmt in MODEL_MEASURES.get(table, []):
        out.append(f"\tmeasure '{name}' = {dax}")
        if fmt:
            out.append(f"\t\tformatString: {fmt}")
        out.append(f"\t\tlineageTag: {uuid.uuid4()}")
        out.append("")
    return "\n".join(out)


def inject_measures(workspace: str, model_id: str) -> None:
    """Pull the model definition, append measures to their tables,
    push back via updateDefinition. Idempotent: skips if present."""
    h = {"Authorization": f"Bearer {_token()}",
         "Content-Type": "application/json"}
    r = requests.post(
        f"{FABRIC}/workspaces/{workspace}/semanticModels/{model_id}/"
        "getDefinition?format=TMDL", headers=h, json={}, timeout=120)
    if r.status_code == 202:
        op = r.headers["Location"]
        for _ in range(24):
            time.sleep(5)
            if requests.get(op, headers=h, timeout=30).json().get(
                    "status") == "Succeeded":
                break
        r = requests.get(op + "/result", headers=h, timeout=60)
    parts = r.json()["definition"]["parts"]
    changed = False
    for p in parts:
        for table in MODEL_MEASURES:
            if p["path"] == f"definition/tables/{table}.tmdl":
                text = base64.b64decode(p["payload"]).decode()
                if "measure '" in text:
                    continue
                block = measures_tmdl(table)
                # measures go inside the table block, before first column
                idx = text.index("\tcolumn ")
                text = text[:idx] + block + "\n" + text[idx:]
                p["payload"] = base64.b64encode(text.encode()).decode()
                changed = True
    if not changed:
        print("measures: already present")
        return
    r = requests.post(
        f"{FABRIC}/workspaces/{workspace}/semanticModels/{model_id}/"
        "updateDefinition", headers=h,
        json={"definition": {"parts": parts}}, timeout=120)
    print("model updateDefinition:", r.status_code)
    if r.status_code == 202:
        op = r.headers["Location"]
        for _ in range(24):
            time.sleep(5)
            s = requests.get(op, headers=h, timeout=30).json()
            if s.get("status") in ("Succeeded", "Failed"):
                print("  op:", s.get("status"))
                if s.get("status") == "Failed":
                    print(json.dumps(s)[:600])
                break


# --- semantic-query builders (PBI prototypeQuery shapes) ---------------

def _col(src: str, prop: str) -> dict:
    return {"Column": {"Expression": {"SourceRef": {"Source": src}},
                       "Property": prop}}


def _countrows(entity_alias: str) -> dict:
    return {"Aggregation": {
        "Expression": {"Column": {
            "Expression": {"SourceRef": {"Source": entity_alias}},
            "Property": None}},
        "Function": 4}}


def card_count(name: str, entity: str, prop: str, pos: dict) -> dict:
    """A card showing COUNT(entity.prop)."""
    alias = entity[0]
    qname = f"Count({entity}.{prop})"
    select = [{"Aggregation": {"Expression": _col(alias, prop),
                               "Function": 4}, "Name": qname}]
    return _container(name, "card", pos,
                      projections={"Values": [{"queryRef": qname}]},
                      entity=entity, alias=alias, select=select)


def table(name: str, entity: str, props: "list[str]", pos: dict) -> dict:
    alias = entity[0]
    select = [{"Column": _col(alias, p)["Column"],
               "Name": f"{entity}.{p}"} for p in props]
    for s in select:
        s.update({"Column": s["Column"]})
    select = [{"Column": _col(alias, p)["Column"], "Name": f"{entity}.{p}"}
              for p in props]
    return _container(
        name, "tableEx", pos,
        projections={"Values": [{"queryRef": f"{entity}.{p}"}
                                for p in props]},
        entity=entity, alias=alias, select=select)


def column_chart(name: str, entity: str, category: str, count_prop: str,
                 pos: dict, function: int = 4) -> dict:
    alias = entity[0]
    cat_name = f"{entity}.{category}"
    agg = {4: "Count", 0: "Sum"}[function]
    val_name = f"{agg}({entity}.{count_prop})"
    select = [
        {"Column": _col(alias, category)["Column"], "Name": cat_name},
        {"Aggregation": {"Expression": _col(alias, count_prop),
                         "Function": function}, "Name": val_name},
    ]
    return _container(
        name, "clusteredColumnChart", pos,
        projections={"Category": [{"queryRef": cat_name}],
                     "Y": [{"queryRef": val_name}]},
        entity=entity, alias=alias, select=select)


def line_chart(name: str, entity: str, axis: str, count_prop: str,
               pos: dict) -> dict:
    alias = entity[0]
    ax_name = f"{entity}.{axis}"
    val_name = f"Count({entity}.{count_prop})"
    select = [
        {"Column": _col(alias, axis)["Column"], "Name": ax_name},
        {"Aggregation": {"Expression": _col(alias, count_prop),
                         "Function": 4}, "Name": val_name},
    ]
    return _container(
        name, "lineChart", pos,
        projections={"Category": [{"queryRef": ax_name}],
                     "Y": [{"queryRef": val_name}]},
        entity=entity, alias=alias, select=select)


def _measure(src_alias: str, prop: str) -> dict:
    return {"Measure": {"Expression": {"SourceRef": {"Source": src_alias}},
                        "Property": prop}}


def card_measure(name: str, entity: str, measure: str, pos: dict) -> dict:
    alias = entity[0]
    qname = f"{entity}.{measure}"
    select = [{"Measure": _measure(alias, measure)["Measure"], "Name": qname}]
    return _container(name, "card", pos,
                      projections={"Values": [{"queryRef": qname}]},
                      entity=entity, alias=alias, select=select)


def bar_measures(name: str, entity: str, measures: "list[str]",
                 pos: dict) -> dict:
    """Horizontal bars, one per measure, in order — the funnel story."""
    alias = entity[0]
    select = [{"Measure": _measure(alias, m)["Measure"],
               "Name": f"{entity}.{m}"} for m in measures]
    return _container(
        name, "clusteredBarChart", pos,
        projections={"Y": [{"queryRef": f"{entity}.{m}"} for m in measures]},
        entity=entity, alias=alias, select=select)


def _bool_filter(entity: str, prop: str, value: str) -> str:
    """Visual-level filter (e.g. failures only)."""
    alias = entity[0]
    return json.dumps([{
        "name": f"flt_{prop}",
        "expression": {"Column": {
            "Expression": {"SourceRef": {"Entity": entity}},
            "Property": prop}},
        "filter": {"Version": 2,
                   "From": [{"Name": alias, "Entity": entity, "Type": 0}],
                   "Where": [{"Condition": {"Comparison": {
                       "ComparisonKind": 0,
                       "Left": {"Column": {
                           "Expression": {"SourceRef": {"Source": alias}},
                           "Property": prop}},
                       "Right": {"Literal": {"Value": value}}}}}]},
        "type": "Categorical", "howCreated": 1,
    }])


def _container(name, visual_type, pos, projections, entity, alias,
               select) -> dict:
    config = {
        "name": name,
        "layouts": [{"id": 0, "position": {**pos, "z": 0}}],
        "singleVisual": {
            "visualType": visual_type,
            "projections": projections,
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": alias, "Entity": entity, "Type": 0}],
                "Select": select,
            },
            "drillFilterOtherVisuals": True,
        },
    }
    return {**pos, "z": 0, "config": json.dumps(config)}


def page(name, display, visuals, ordinal) -> dict:
    return {
        "name": name, "displayName": display, "displayOption": 1,
        "height": 720.0, "width": 1280.0, "ordinal": ordinal,
        "visualContainers": visuals,
        "config": "{}", "filters": "[]",
    }


# --- the four pages ----------------------------------------------------

def build_report_json() -> dict:
    HALF = {"width": 620.0, "height": 300.0}
    WIDE = {"width": 1240.0, "height": 360.0}
    CARD = {"width": 300.0, "height": 120.0}

    p1 = page("p1", "Pipeline Health", [
        card_measure("v10", "ops_build_summary", "Last Build",
                     {"x": 20.0, "y": 20.0, **CARD}),
        card_measure("v11", "ops_pipeline_validation", "Metrics Fully Valid",
                     {"x": 340.0, "y": 20.0, **CARD}),
        card_measure("v1b", "ops_installation_errors", "Errors On Record",
                     {"x": 660.0, "y": 20.0, **CARD}),
        bar_measures("v1f", "ops_pipeline_validation",
                     [f"Passed {label}" for label in STEP_LABELS],
                     {"x": 20.0, "y": 160.0, "width": 620.0,
                      "height": 340.0}),
        {**{"x": 660.0, "y": 160.0, "width": 600.0, "height": 340.0,
            "z": 0},
         "config": table("v1m", "ops_pipeline_validation",
                         ["metric_id"] + VALIDATION_STEPS,
                         {"x": 660.0, "y": 160.0, "width": 600.0,
                          "height": 340.0})["config"],
         "filters": _bool_filter("ops_pipeline_validation",
                                 "step6_traversal", "false")},
        table("v13", "ops_installation_errors",
              ["error_category", "error_signature", "root_cause", "fix",
               "first_seen"],
              {"x": 20.0, "y": 520.0, "width": 1240.0, "height": 180.0}),
    ], 0)

    p2 = page("p2", "Knowledge Coverage", [
        card_measure("v21", "output_metric_logic", "Certified Metrics",
                     {"x": 20.0, "y": 20.0, **CARD}),
        card_measure("v22", "ops_parse_results", "Objects Parsed",
                     {"x": 340.0, "y": 20.0, **CARD}),
        card_measure("v2s", "output_metric_logic",
                     "Total Calculation Steps",
                     {"x": 660.0, "y": 20.0, **CARD}),
        bar_measures("v2g", "output_metric_logic",
                     ["Pct With Description", "Pct With Business Name",
                      "Pct With Steward", "Pct With Developer",
                      "Pct With Report Link"],
                     {"x": 20.0, "y": 160.0, "width": 620.0,
                      "height": 320.0}),
        card_measure("v2m", "output_metric_logic", "Missing Steward",
                     {"x": 660.0, "y": 160.0, **CARD}),
        table("v23", "output_metric_logic",
              ["metric_id", "business_name", "steward", "developer",
               "report_name"],
              {"x": 660.0, "y": 300.0, "width": 600.0, "height": 180.0}),
        column_chart("v2c", "output_metric_logic", "metric_id",
                     "transform_count",
                     {"x": 20.0, "y": 500.0, "width": 1240.0,
                      "height": 200.0}, function=0),
    ], 1)

    p3 = page("p3", "Agent Activity & Decisions", [
        card_measure("v31", "gov_turn_events", "Turns",
                     {"x": 20.0, "y": 20.0, **CARD}),
        card_measure("v3u", "gov_turn_events", "Distinct Users",
                     {"x": 340.0, "y": 20.0, **CARD}),
        card_measure("v3z", "gov_turn_events",
                     "Unverified Sameness Claims",
                     {"x": 660.0, "y": 20.0, **CARD}),
        card_measure("v3e", "gov_turn_events", "Tool Errors",
                     {"x": 980.0, "y": 20.0, **CARD}),
        bar_measures("v3d", "gov_turn_events",
                     ["Verified By Tool", "LLM Assembled", "Search Only",
                      "No Tools"],
                     {"x": 20.0, "y": 160.0, "width": 620.0,
                      "height": 300.0}),
        line_chart("v3t", "gov_turn_events", "event_at", "conversation_id",
                   {"x": 660.0, "y": 160.0, "width": 600.0,
                    "height": 300.0}),
        table("v34", "gov_turn_events",
              ["event_at", "user_id", "question", "tools_used",
               "verified_by_tool"],
              {"x": 20.0, "y": 480.0, "width": 1240.0, "height": 220.0}),
    ], 2)

    p4 = page("p4", "Feedback & Governance", [
        card_measure("v41", "gov_feedback_events", "Feedback Events",
                     {"x": 20.0, "y": 20.0, **CARD}),
        card_measure("v4n", "gov_feedback_events", "Not Helpful",
                     {"x": 340.0, "y": 20.0, **CARD}),
        column_chart("v42", "gov_feedback_events", "verdict", "event_at",
                     {"x": 20.0, "y": 160.0, **HALF}),
        table("v43", "gov_feedback_events",
              ["event_at", "user_id", "verdict", "comment"],
              {"x": 660.0, "y": 160.0, "width": 600.0, "height": 300.0}),
        table("v44", "gov_turn_events",
              ["event_at", "question", "verified_by_tool", "llm_assembled",
               "search_only", "no_tools"],
              {"x": 20.0, "y": 480.0, "width": 1240.0, "height": 220.0}),
        # gov_publish_log joins this page once 08/09 first writes it
        # (table does not exist in lakehouse or model yet — honest gap)
    ], 3)

    return {
        "config": json.dumps({"version": "5.43", "themeCollection": {}}),
        "layoutOptimization": 0,
        "sections": [p1, p2, p3, p4],
    }


def definition_pbir(model_id: str) -> dict:
    return {"version": "1.0", "datasetReference": {"byConnection": {
        "connectionString": None,
        "pbiServiceModelId": None,
        "pbiModelVirtualServerName": "sobe_wowvirtualserver",
        "pbiModelDatabaseName": model_id,
        "name": "EntityDataSource",
        "connectionType": "pbiServiceXmlaStyleLive"}}}


# --- deployment ---------------------------------------------------------

def _token() -> str:
    return subprocess.run(
        ["az", "account", "get-access-token", "--resource",
         "https://api.fabric.microsoft.com", "--query", "accessToken",
         "-o", "tsv"], capture_output=True, text=True, check=True,
    ).stdout.strip()


def _b64(obj) -> str:
    return base64.b64encode(
        json.dumps(obj, indent=1).encode()).decode()


def deploy(workspace: str, model_id: str, name: str) -> None:
    parts = [
        {"path": "report.json", "payload": _b64(build_report_json()),
         "payloadType": "InlineBase64"},
        {"path": "definition.pbir", "payload": _b64(definition_pbir(model_id)),
         "payloadType": "InlineBase64"},
    ]
    h = {"Authorization": f"Bearer {_token()}",
         "Content-Type": "application/json"}
    r = requests.post(
        f"{FABRIC}/workspaces/{workspace}/reports", headers=h,
        json={"displayName": name, "definition": {"parts": parts}},
        timeout=120)
    print("create:", r.status_code)
    if r.status_code == 202:
        op = r.headers.get("Location", "")
        for _ in range(24):
            time.sleep(5)
            s = requests.get(op, headers=h, timeout=30).json()
            print("  op:", s.get("status"))
            if s.get("status") in ("Succeeded", "Failed"):
                if s.get("status") == "Failed":
                    print(json.dumps(s, indent=1)[:800])
                return
    elif not r.ok:
        print(r.text[:800])


def update_report(workspace: str, model_id: str, report_id: str) -> None:
    parts = [
        {"path": "report.json", "payload": _b64(build_report_json()),
         "payloadType": "InlineBase64"},
        {"path": "definition.pbir", "payload": _b64(definition_pbir(model_id)),
         "payloadType": "InlineBase64"},
    ]
    h = {"Authorization": f"Bearer {_token()}",
         "Content-Type": "application/json"}
    r = requests.post(
        f"{FABRIC}/workspaces/{workspace}/reports/{report_id}/"
        "updateDefinition", headers=h,
        json={"definition": {"parts": parts}}, timeout=120)
    print("report updateDefinition:", r.status_code)
    if r.status_code == 202:
        op = r.headers["Location"]
        for _ in range(24):
            time.sleep(5)
            s = requests.get(op, headers=h, timeout=30).json()
            if s.get("status") in ("Succeeded", "Failed"):
                print("  op:", s.get("status"))
                if s.get("status") == "Failed":
                    print(json.dumps(s)[:800])
                break
    elif not r.ok:
        print(r.text[:800])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--name", default="aivia_admin_telemetry_report")
    ap.add_argument("--report", help="existing report id -> updateDefinition")
    ap.add_argument("--skip-measures", action="store_true")
    a = ap.parse_args()
    if not a.skip_measures:
        inject_measures(a.workspace, a.model)
    if a.report:
        update_report(a.workspace, a.model, a.report)
    else:
        deploy(a.workspace, a.model, a.name)
