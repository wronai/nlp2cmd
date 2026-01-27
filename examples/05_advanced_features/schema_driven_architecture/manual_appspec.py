from __future__ import annotations

import json
from pathlib import Path

from nlp2cmd.appspec_runtime import load_appspec
from nlp2cmd.schema_driven import SchemaDrivenNLP2CMD


def main() -> None:
    appspec_path = Path("./manual_appspec.json")

    appspec = {
        "format": "app2schema.appspec",
        "version": 1,
        "app": {"name": "demo", "kind": "mixed", "source": "manual", "metadata": {}},
        "actions": [
            {
                "id": "sql.query",
                "type": "sql",
                "description": "SQL query",
                "dsl": {
                    "kind": "sql",
                    "dialect": "postgres",
                    "output_format": "table",
                    "template": "SELECT id, name, email FROM users WHERE email LIKE '%@{domain}';",
                },
                "params": {
                    "domain": {"type": "string", "required": True, "location": "unknown"}
                },
                "schema": {
                    "tables": {
                        "users": ["id", "name", "email", "created_at"],
                        "orders": ["id", "user_id", "amount", "status"],
                    }
                },
                "match": {"patterns": ["pokaż użytkowników", "show users"], "examples": []},
                "executor": {"kind": "sql", "config": {"db": "postgres"}},
                "metadata": {},
            },
            {
                "id": "graphql.query",
                "type": "graphql",
                "description": "GraphQL query",
                "dsl": {
                    "kind": "graphql",
                    "output_format": "json",
                    "template": "query { users(filter: {name_starts_with: \"{prefix}\"}) { id name email } }",
                },
                "params": {"prefix": {"type": "string", "required": True}},
                "schema": {
                    "endpoint": "https://api.example.com/graphql",
                    "types": {"User": ["id", "name", "email"]},
                },
                "match": {"patterns": ["pobierz użytkowników"], "examples": []},
                "executor": {"kind": "graphql", "config": {}},
                "metadata": {},
            },
            {
                "id": "dom.query",
                "type": "dom",
                "description": "DOM selector",
                "dsl": {
                    "kind": "dom",
                    "output_format": "raw",
                    "template": "#login-section button:first-of-type",
                },
                "params": {},
                "schema": {"supports": ["css", "xpath"]},
                "match": {"patterns": ["kliknij pierwszy przycisk"], "examples": []},
                "executor": {"kind": "playwright", "config": {"action": "click"}},
                "metadata": {},
            },
            {
                "id": "shell.run",
                "type": "shell",
                "description": "Shell command",
                "dsl": {"kind": "shell", "output_format": "raw", "template": "ls -lS | head -n {n}"},
                "params": {"n": {"type": "integer", "required": True}},
                "schema": {"shell": "bash"},
                "match": {"patterns": ["10 największych"], "examples": []},
                "executor": {"kind": "shell", "config": {"shell": "bash"}},
                "metadata": {},
            },
        ],
        "metadata": {},
    }

    appspec_path.write_text(json.dumps(appspec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    spec = load_appspec(appspec_path)
    engine = SchemaDrivenNLP2CMD(spec)

    # MVP param extraction expects key=value tokens
    print(engine.transform("pokaż użytkowników domain=example.com").dsl)
    print(engine.transform("pobierz użytkowników prefix=A").dsl)
    print(engine.transform("kliknij pierwszy przycisk").dsl)
    print(engine.transform("10 największych n=10").dsl)


if __name__ == "__main__":
    main()
