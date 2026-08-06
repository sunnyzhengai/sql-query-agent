"""Tests for the deployment pre-flight validator."""

from pathlib import Path

from scripts.validate_deployment import (
    check_dictionary,
    check_llm,
    check_org_config,
    check_scriptdom,
    check_sql_input,
    validate,
)


def make_good_root(tmp_path: Path) -> Path:
    root = tmp_path / "deploy"
    (root / "dictionary").mkdir(parents=True)
    (root / "sql_input").mkdir()
    (root / "libs").mkdir()
    (root / "org_config.yaml").write_text(
        "org:\n  name: Test Hospital\n"
        "llm:\n  endpoint: https://api.openai.com/v1\n"
        "  model: gpt-4o-mini\n  api_key_file: llm_api_key.txt\n"
    )
    (root / "llm_api_key.txt").write_text("sk-test-123\n")
    (root / "dictionary" / "dict_tables.csv").write_text(
        "TABLE_NAME,DESCRIPTION\nENCOUNTERS,Hospital encounters\n"
    )
    (root / "dictionary" / "dict_columns.csv").write_text(
        "TABLE_NAME,COLUMN_NAME,DESCRIPTION\nENCOUNTERS,CSN,Contact serial\n"
    )
    (root / "sql_input" / "usp_metric.sql").write_text("SELECT 1")
    (root / "libs" / "Microsoft.SqlServer.TransactSql.ScriptDom.dll").write_bytes(b"x")
    return root


def levels(results):
    return {r.name: r.level for r in results}


class TestHappyPath:
    def test_good_root_has_no_failures(self, tmp_path):
        results = validate(make_good_root(tmp_path))
        assert not [r for r in results if r.level == "fail"], levels(results)


class TestFailures:
    def test_missing_root_fails_fast(self, tmp_path):
        results = validate(tmp_path / "nope")
        assert results[-1].level == "fail"
        assert len(results) == 2  # python + root, nothing else attempted

    def test_missing_dictionary_is_fatal(self, tmp_path):
        root = make_good_root(tmp_path)
        (root / "dictionary" / "dict_tables.csv").unlink()
        results = check_dictionary(root)
        assert results[0].level == "fail"
        assert "MANDATORY" in results[0].message

    def test_dictionary_missing_column_fails(self, tmp_path):
        root = make_good_root(tmp_path)
        (root / "dictionary" / "dict_columns.csv").write_text(
            "TABLE_NAME,DESCRIPTION\nX,Y\n"  # no COLUMN_NAME
        )
        results = check_dictionary(root)
        assert results[1].level == "fail"
        assert "COLUMN_NAME" in results[1].message

    def test_empty_dictionary_fails(self, tmp_path):
        root = make_good_root(tmp_path)
        (root / "dictionary" / "dict_tables.csv").write_text("TABLE_NAME,DESCRIPTION\n")
        assert check_dictionary(root)[0].level == "fail"

    def test_no_sql_files_fails(self, tmp_path):
        root = make_good_root(tmp_path)
        (root / "sql_input" / "usp_metric.sql").unlink()
        assert check_sql_input(root).level == "fail"

    def test_unparseable_config_fails(self, tmp_path):
        root = make_good_root(tmp_path)
        (root / "org_config.yaml").write_text("org: [unclosed")
        result, cfg = check_org_config(root)
        assert result.level == "fail" and cfg == {}


class TestLlmChecks:
    def test_missing_llm_block_is_warning_not_failure(self, tmp_path):
        root = make_good_root(tmp_path)
        results = check_llm(root, {"org": {"name": "X"}})
        assert results[0].level == "warn"
        assert "07" in results[0].message

    def test_missing_key_file_fails(self, tmp_path):
        root = make_good_root(tmp_path)
        (root / "llm_api_key.txt").unlink()
        results = check_llm(root, {"llm": {"endpoint": "https://api.openai.com/v1"}})
        assert any(r.level == "fail" and "api_key" in r.name for r in results)

    def test_env_style_key_file_fails(self, tmp_path):
        root = make_good_root(tmp_path)
        (root / "llm_api_key.txt").write_text("OPENAI_API_KEY=sk-123\n")
        results = check_llm(root, {"llm": {"endpoint": "https://api.openai.com/v1"}})
        assert any(r.level == "fail" and "raw key" in r.message for r in results)

    def test_http_endpoint_fails(self, tmp_path):
        root = make_good_root(tmp_path)
        results = check_llm(root, {"llm": {"endpoint": "http://api.openai.com/v1"}})
        assert any(r.level == "fail" and "https" in r.message for r in results)

    def test_azure_endpoint_without_api_version_warns(self, tmp_path):
        root = make_good_root(tmp_path)
        results = check_llm(root, {"llm": {
            "endpoint": "https://myres.openai.azure.com/openai/deployments/gpt4",
        }})
        assert any(r.level == "warn" and "api-version" in r.message for r in results)


class TestWarnings:
    def test_missing_dll_warns_not_fails(self, tmp_path):
        root = make_good_root(tmp_path)
        (root / "libs" / "Microsoft.SqlServer.TransactSql.ScriptDom.dll").unlink()
        assert check_scriptdom(root).level == "warn"

    def test_example_org_name_warns(self, tmp_path):
        root = make_good_root(tmp_path)
        (root / "org_config.yaml").write_text("org:\n  name: Example Health System\n")
        result, _ = check_org_config(root)
        assert result.level == "warn"
