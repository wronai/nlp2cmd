#!/usr/bin/env python3
"""
Dynamic sources example: Shell script + Makefile.

This example demonstrates the intended flow:
1) app2schema: extract schema from local sources (.sh, Makefile)
2) nlp2cmd: import the generated dynamic schema export into DynamicAdapter
3) transform: generate commands using schema-driven dynamic routing
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from app2schema import extract_schema_to_file
from nlp2cmd.adapters.dynamic import DynamicAdapter
from nlp2cmd.core import NLP2CMD


def main() -> None:
    tmp_dir = Path(tempfile.mkdtemp(prefix="nlp2cmd_dynamic_sources_"))

    sh_path = tmp_dir / "demo.sh"
    sh_path.write_text(
        """#!/usr/bin/env bash
# Demo script
# Usage: demo.sh [--name NAME] [-v]

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)
      NAME="$2"; shift 2;;
    -v)
      VERBOSE=1; shift;;
    *)
      shift;;
  esac
done
""",
        encoding="utf-8",
    )

    mk_path = tmp_dir / "Makefile"
    mk_path.write_text(
        """# Demo Makefile
+.PHONY: test
+test:
+\techo running tests
+""",
        encoding="utf-8",
    )

    export_path = tmp_dir / "dynamic_export.json"

    # app2schema: produce a validated dynamic schema export (single file)
    extract_schema_to_file(str(sh_path), export_path, source_type="shell_script")
    extract_schema_to_file(str(mk_path), export_path, source_type="makefile")

    # nlp2cmd: import exported schemas
    adapter = DynamicAdapter(config={"custom_options": {"load_common_commands": False}})
    adapter.register_schema_source(str(export_path), source_type="auto")
    nlp = NLP2CMD(adapter=adapter)

    # Transform examples
    print("=== Commands available ===")
    print([c.name for c in adapter.registry.get_all_commands()])

    print("\n=== Transform examples ===")
    print(nlp.transform("run make test").command)
    print(nlp.transform("run demo script with verbose").command)

    print("\n=== Export preview ===")
    payload = json.loads(export_path.read_text(encoding="utf-8"))
    print(f"sources: {list((payload.get('sources') or {}).keys())}")


if __name__ == "__main__":
    main()
