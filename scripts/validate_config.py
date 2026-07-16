"""Pre-flight check: validate org_config.yaml."""

import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import load_config


def main() -> None:
    try:
        config = load_config()
        print(f"Config valid for org: {config.org.name}")
        print(f"  Lakehouse paths:")
        print(f"    dict_tables:  {config.lakehouse.dict_tables}")
        print(f"    dict_columns: {config.lakehouse.dict_columns}")
        print(f"    sql_sources:  {config.lakehouse.sql_sources}")
        print(f"    graph_nodes:  {config.lakehouse.graph_nodes}")
        print(f"    graph_edges:  {config.lakehouse.graph_edges}")
        print(f"  Dictionary column mapping:")
        print(f"    table_name:  {config.dictionary.table_name_col}")
        print(f"    column_name: {config.dictionary.column_name_col}")
        print(f"    description: {config.dictionary.description_col}")
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Invalid config: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
