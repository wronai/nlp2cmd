from __future__ import annotations


def print_separator(
    title: str,
    *,
    leading_newline: bool = False,
    width: int = 70,
) -> None:
    prefix = "\n" if leading_newline else ""
    print(f"{prefix}{'=' * width}")
    print(f"{title}")
    print("=" * width)


def print_rule(
    *,
    width: int = 50,
    char: str = "-",
    indent: str = "",
    leading_newline: bool = False,
) -> None:
    prefix = "\n" if leading_newline else ""
    print(f"{prefix}{indent}{char * width}")
