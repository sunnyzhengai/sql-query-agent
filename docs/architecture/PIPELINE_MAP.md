<!-- GENERATED FILE — do not edit.
     Source: TABLE_REGISTRY in src/schemas.py
     Regenerate: python scripts/generate_docs.py
     CI fails if this file differs from regeneration. -->

# Pipeline Dataflow Map

Every edge below is a declared, code-verified fact from the data contracts:
solid arrows into a table are its owner/enricher writes, dashed arrows are
sanctioned utility writers, and arrows out of a table are its declared
consumers (notebook reads are verified against code by the contract tests).

```mermaid
flowchart LR
  010_ingest_sql_filedrop["010_ingest_sql_filedrop"]:::notebook
  020_ingest_sql_folders["020_ingest_sql_folders"]:::notebook
  030_ingest_sql_live["030_ingest_sql_live"]:::notebook
  040_dict_clarity["040_dict_clarity"]:::notebook
  050_dict_caboodle["050_dict_caboodle"]:::notebook
  060_ingest_semantic_models["060_ingest_semantic_models"]:::notebook
  100_install["100_install"]:::notebook
  200_parse["200_parse"]:::notebook
  300_build_graph["300_build_graph"]:::notebook
  400_build_metric_logic["400_build_metric_logic"]:::notebook
  500_validate["500_validate"]:::notebook
  600_generate_descriptions["600_generate_descriptions"]:::notebook
  610_generate_agent_descriptions["610_generate_agent_descriptions"]:::notebook
  700_refresh_search_index["700_refresh_search_index"]:::notebook
  800_export_graph_tables["800_export_graph_tables"]:::notebook
  900_publish_collibra["900_publish_collibra"]:::notebook
  910_publish_purview["910_publish_purview"]:::notebook
  920_publish_pbi["920_publish_pbi"]:::notebook
  950_ingest_agent_events["950_ingest_agent_events"]:::notebook
  admin_companion["admin_companion"]:::notebook
  collibra_lineage_match["collibra_lineage_match"]:::notebook
  description["description"]:::notebook
  eventhouse_semantic_search["eventhouse_semantic_search"]:::notebook
  export_test_fixtures["export_test_fixtures"]:::notebook
  health["health"]:::notebook
  manage_stewards["manage_stewards"]:::notebook
  orchestrator_core["orchestrator_core"]:::notebook
  self_service["self-service"]:::notebook
  usage["usage"]:::notebook
  verify_graph["verify_graph"]:::notebook
  LPG_export__14_typed_tables_[("LPG export (14 typed tables)")]:::table
  gov_feedback_events[("gov_feedback_events")]:::table
  gov_publish_log[("gov_publish_log")]:::table
  gov_steward_assignments[("gov_steward_assignments")]:::table
  gov_turn_events[("gov_turn_events")]:::table
  graph_decision_sites[("graph_decision_sites")]:::table
  graph_edges[("graph_edges")]:::table
  graph_nodes[("graph_nodes")]:::table
  input_dax_expressions[("input_dax_expressions")]:::table
  input_dict_columns[("input_dict_columns")]:::table
  input_dict_tables[("input_dict_tables")]:::table
  input_metric_names[("input_metric_names")]:::table
  input_report_sources[("input_report_sources")]:::table
  input_sql_sources[("input_sql_sources")]:::table
  ops_admin_graph_edges[("ops_admin_graph_edges")]:::table
  ops_admin_graph_nodes[("ops_admin_graph_nodes")]:::table
  ops_agent_descriptions[("ops_agent_descriptions")]:::table
  ops_build_summary[("ops_build_summary")]:::table
  ops_description_cache[("ops_description_cache")]:::table
  ops_error_log[("ops_error_log")]:::table
  ops_extraction_tracking[("ops_extraction_tracking")]:::table
  ops_fallout[("ops_fallout")]:::table
  ops_funnel[("ops_funnel")]:::table
  ops_installation_errors[("ops_installation_errors")]:::table
  ops_metric_journey[("ops_metric_journey")]:::table
  ops_parse_errors[("ops_parse_errors")]:::table
  ops_parse_results[("ops_parse_results")]:::table
  ops_parse_successes[("ops_parse_successes")]:::table
  ops_phi_findings[("ops_phi_findings")]:::table
  ops_pipeline_validation[("ops_pipeline_validation")]:::table
  ops_report_journey[("ops_report_journey")]:::table
  ops_setup_completeness[("ops_setup_completeness")]:::table
  output_metric_logic[("output_metric_logic")]:::table
  output_metric_twins[("output_metric_twins")]:::table
  output_semantic_catalog[("output_semantic_catalog")]:::table
  admin{{admin}}:::actor
  collibra_adapter{{collibra_adapter}}:::actor
  data_agent{{data_agent}}:::actor
  010_ingest_sql_filedrop --> input_sql_sources
  020_ingest_sql_folders -.-> input_sql_sources
  030_ingest_sql_live --> ops_extraction_tracking
  030_ingest_sql_live -.-> input_sql_sources
  040_dict_clarity --> input_dict_columns
  040_dict_clarity --> input_dict_tables
  050_dict_caboodle -.-> input_dict_columns
  050_dict_caboodle -.-> input_dict_tables
  060_ingest_semantic_models --> input_dax_expressions
  060_ingest_semantic_models --> input_metric_names
  060_ingest_semantic_models --> input_report_sources
  060_ingest_semantic_models --> ops_fallout
  100_install --> ops_installation_errors
  200_parse --> ops_error_log
  200_parse --> ops_parse_errors
  200_parse --> ops_parse_results
  200_parse --> ops_parse_successes
  200_parse --> ops_phi_findings
  300_build_graph --> graph_decision_sites
  300_build_graph --> graph_edges
  300_build_graph --> graph_nodes
  300_build_graph --> ops_setup_completeness
  300_build_graph -->|enrich| ops_fallout
  400_build_metric_logic --> output_metric_logic
  400_build_metric_logic --> output_metric_twins
  500_validate --> ops_admin_graph_edges
  500_validate --> ops_admin_graph_nodes
  500_validate --> ops_build_summary
  500_validate --> ops_funnel
  500_validate --> ops_metric_journey
  500_validate --> ops_pipeline_validation
  500_validate --> ops_report_journey
  500_validate -->|enrich| ops_fallout
  600_generate_descriptions --> ops_description_cache
  600_generate_descriptions -->|enrich| graph_nodes
  600_generate_descriptions -->|enrich| ops_fallout
  600_generate_descriptions -->|enrich| output_metric_logic
  610_generate_agent_descriptions --> ops_agent_descriptions
  700_refresh_search_index --> output_semantic_catalog
  800_export_graph_tables --> LPG_export__14_typed_tables_
  900_publish_collibra --> gov_publish_log
  900_publish_collibra -->|enrich| ops_fallout
  910_publish_purview -->|enrich| gov_publish_log
  920_publish_pbi -->|enrich| gov_publish_log
  950_ingest_agent_events --> gov_feedback_events
  950_ingest_agent_events --> gov_turn_events
  gov_feedback_events --> 950_ingest_agent_events
  gov_feedback_events --> admin
  gov_feedback_events --> usage
  gov_publish_log --> 500_validate
  gov_publish_log --> admin
  gov_steward_assignments --> 300_build_graph
  gov_steward_assignments --> manage_stewards
  gov_turn_events --> 950_ingest_agent_events
  gov_turn_events --> admin
  gov_turn_events --> usage
  graph_decision_sites --> admin
  graph_decision_sites --> description
  graph_decision_sites --> self_service
  graph_edges --> 400_build_metric_logic
  graph_edges --> 500_validate
  graph_edges --> 600_generate_descriptions
  graph_edges --> 800_export_graph_tables
  graph_edges --> 900_publish_collibra
  graph_edges --> 920_publish_pbi
  graph_edges --> data_agent
  graph_edges --> verify_graph
  graph_nodes --> 400_build_metric_logic
  graph_nodes --> 500_validate
  graph_nodes --> 600_generate_descriptions
  graph_nodes --> 610_generate_agent_descriptions
  graph_nodes --> 700_refresh_search_index
  graph_nodes --> 800_export_graph_tables
  graph_nodes --> 900_publish_collibra
  graph_nodes --> 920_publish_pbi
  graph_nodes --> data_agent
  graph_nodes --> manage_stewards
  graph_nodes --> verify_graph
  input_dax_expressions --> 300_build_graph
  input_dict_columns --> 050_dict_caboodle
  input_dict_columns --> 300_build_graph
  input_dict_columns --> export_test_fixtures
  input_dict_tables --> 050_dict_caboodle
  input_dict_tables --> 100_install
  input_dict_tables --> 300_build_graph
  input_dict_tables --> 500_validate
  input_dict_tables --> export_test_fixtures
  input_metric_names --> 300_build_graph
  input_metric_names --> collibra_lineage_match
  input_report_sources --> 300_build_graph
  input_report_sources --> 500_validate
  input_sql_sources --> 020_ingest_sql_folders
  input_sql_sources --> 060_ingest_semantic_models
  input_sql_sources --> 100_install
  input_sql_sources --> 200_parse
  input_sql_sources --> 500_validate
  manage_stewards --> gov_steward_assignments
  ops_admin_graph_edges --> admin_companion
  ops_admin_graph_nodes --> admin_companion
  ops_agent_descriptions --> 500_validate
  ops_agent_descriptions --> 610_generate_agent_descriptions
  ops_agent_descriptions --> 900_publish_collibra
  ops_agent_descriptions --> 920_publish_pbi
  ops_agent_descriptions --> collibra_adapter
  ops_build_summary --> admin
  ops_description_cache --> 600_generate_descriptions
  ops_error_log --> 200_parse
  ops_error_log --> admin
  ops_extraction_tracking --> 030_ingest_sql_live
  ops_fallout --> 500_validate
  ops_fallout --> admin
  ops_funnel --> admin
  ops_installation_errors --> data_agent
  ops_metric_journey --> admin
  ops_parse_errors --> 500_validate
  ops_parse_errors --> data_agent
  ops_parse_errors --> verify_graph
  ops_parse_results --> 300_build_graph
  ops_parse_results --> 500_validate
  ops_parse_results --> export_test_fixtures
  ops_parse_successes --> 200_parse
  ops_parse_successes --> 500_validate
  ops_parse_successes --> verify_graph
  ops_phi_findings --> 200_parse
  ops_phi_findings --> 600_generate_descriptions
  ops_pipeline_validation --> 500_validate
  ops_pipeline_validation --> admin
  ops_pipeline_validation --> data_agent
  ops_report_journey --> admin
  ops_setup_completeness --> admin
  ops_setup_completeness --> health
  output_metric_logic --> 400_build_metric_logic
  output_metric_logic --> 500_validate
  output_metric_logic --> 600_generate_descriptions
  output_metric_logic --> 610_generate_agent_descriptions
  output_metric_logic --> 910_publish_purview
  output_metric_logic --> data_agent
  output_metric_twins --> data_agent
  output_semantic_catalog --> data_agent
  output_semantic_catalog --> eventhouse_semantic_search
  output_semantic_catalog --> orchestrator_core
  classDef notebook fill:#e8f0fe,stroke:#4285f4
  classDef table fill:#fef7e0,stroke:#f9ab00
  classDef actor fill:#e6f4ea,stroke:#34a853
```

Planned tables (contracts without writers) and per-table details — columns,
invariants, relations — live in `src/schemas.py`.
