from __future__ import annotations

import json
from pathlib import Path

from app2schema import extract_appspec_to_file
from nlp2cmd.adapters import AppSpecAdapter
from nlp2cmd.core import NLP2CMD


def main() -> None:
    # Example: create an AppSpec from a shell command
    appspec_path = Path("./generated_appspec.json")
    extract_appspec_to_file("git", appspec_path)

    adapter = AppSpecAdapter(appspec_path=appspec_path)
    nlp2cmd = NLP2CMD(adapter=adapter)

    ir = nlp2cmd.transform_ir("show git status")
    print(json.dumps(ir.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
