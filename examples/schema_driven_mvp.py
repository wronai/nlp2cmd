from __future__ import annotations

import json
from pathlib import Path

from app2schema import extract_appspec_to_file
from nlp2cmd.appspec_runtime import load_appspec
from nlp2cmd.schema_driven import SchemaDrivenNLP2CMD


def main() -> None:
    appspec_path = Path("./generated_appspec.json")

    # Example: build AppSpec from an OpenAPI or from a shell command
    # - shell example:
    extract_appspec_to_file("git", appspec_path)

    spec = load_appspec(appspec_path)
    engine = SchemaDrivenNLP2CMD(spec)

    ir = engine.transform("show git status")
    print(json.dumps(ir.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
