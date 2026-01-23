from __future__ import annotations

import json
from pathlib import Path

from app2schema.extract import extract_schema_to_file
from nlp2cmd.adapters.dynamic import DynamicAdapter
from nlp2cmd.core import NLP2CMD


def main() -> None:
    # Example 1: create a schema from a shell command
    out_git = Path("./generated_app2schema_git.json")
    out_df = Path("./generated_app2schema_df.json")
    extract_schema_to_file("git", out_git, source_type="shell")
    extract_schema_to_file("df", out_df, source_type="shell")

    # Load schema into DynamicAdapter
    adapter = DynamicAdapter()
    adapter.register_schema_source(str(out_git), source_type="auto")
    adapter.register_schema_source(str(out_df), source_type="auto")

    # Use NLP2CMD on top
    nlp2cmd = NLP2CMD(adapter=adapter)

    result = nlp2cmd.transform("show git status")
    print(result.command)

    # Optional: print imported schema summary
    data_git = json.loads(out_git.read_text(encoding="utf-8"))
    data_df = json.loads(out_df.read_text(encoding="utf-8"))
    print(f"Imported sources (git): {list((data_git.get('sources') or {}).keys())}")
    print(f"Imported sources (df): {list((data_df.get('sources') or {}).keys())}")


if __name__ == "__main__":
    main()
