from __future__ import annotations

import json
from pathlib import Path

from app2schema.extract import extract_schema_to_file
from nlp2cmd.adapters.dynamic import DynamicAdapter
from nlp2cmd.core import NLP2CMD


def main() -> None:
    # Example 1: create a schema from a shell command
    out = Path("./generated_app2schema.json")
    extract_schema_to_file("git", out)

    # Load schema into DynamicAdapter
    adapter = DynamicAdapter()
    adapter.register_schema_source(str(out), source_type="auto")

    # Use NLP2CMD on top
    nlp2cmd = NLP2CMD(adapter=adapter)

    result = nlp2cmd.transform("show git status")
    print(result.command)

    # Optional: print imported schema summary
    data = json.loads(out.read_text(encoding="utf-8"))
    print(f"Imported sources: {list((data.get('sources') or {}).keys())}")


if __name__ == "__main__":
    main()
