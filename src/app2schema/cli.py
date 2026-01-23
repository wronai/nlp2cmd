from __future__ import annotations

from pathlib import Path

import click

from app2schema.extract import extract_schema_to_file


@click.command()
@click.argument("target")
@click.option(
    "--type",
    "source_type",
    type=click.Choice(["auto", "openapi", "shell", "python"], case_sensitive=False),
    default="auto",
)
@click.option(
    "-o",
    "--out",
    "out_path",
    type=click.Path(dir_okay=False, path_type=Path),
    required=True,
)
@click.option("--raw", is_flag=True)
@click.option("--no-discover", is_flag=True)
def main(target: str, source_type: str, out_path: Path, raw: bool, no_discover: bool) -> None:
    written = extract_schema_to_file(
        target,
        out_path,
        source_type=source_type,  # type: ignore[arg-type]
        discover_openapi=not no_discover,
        raw=raw,
    )
    click.echo(str(written))


if __name__ == "__main__":
    main()
