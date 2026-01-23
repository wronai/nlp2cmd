from __future__ import annotations

from pathlib import Path

import click

from app2schema.extract import extract_appspec_to_file


@click.command()
@click.argument("target")
@click.option(
    "--type",
    "source_type",
    type=click.Choice(
        [
            "auto",
            "openapi",
            "shell",
            "python",
            "python_package",
            "shell_script",
            "makefile",
            "web",
            "web_runtime",
        ],
        case_sensitive=False,
    ),
    default="auto",
)
@click.option("--merge", is_flag=True)
@click.option(
    "-o",
    "--out",
    "out_path",
    type=click.Path(dir_okay=False, path_type=Path),
    required=True,
)
@click.option("--no-validate", is_flag=True)
@click.option("--no-discover", is_flag=True)
def main(
    target: str,
    source_type: str,
    out_path: Path,
    merge: bool,
    no_validate: bool,
    no_discover: bool,
) -> None:
    written = extract_appspec_to_file(
        target,
        out_path,
        source_type=source_type,  # type: ignore[arg-type]
        discover_openapi=not no_discover,
        validate=not no_validate,
        merge=merge,
    )
    click.echo(str(written))


if __name__ == "__main__":
    main()
