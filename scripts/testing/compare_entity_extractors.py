from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _ensure_src_on_path() -> None:
    src = _repo_root() / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def _load_dataset(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _diff_entities(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    keys = set(a.keys()) | set(b.keys())
    changed: dict[str, Any] = {}
    for k in sorted(keys):
        av = a.get(k)
        bv = b.get(k)
        if av != bv:
            changed[k] = {"regex": av, "semantic": bv}
    return changed


def _set_extractor_env(mode: Optional[str], ab_ratio: Optional[str]) -> dict[str, Optional[str]]:
    prev_mode = os.environ.get("NLP2CMD_ENTITY_EXTRACTOR_MODE")
    prev_ratio = os.environ.get("NLP2CMD_ENTITY_AB_RATIO")

    if mode is None:
        os.environ.pop("NLP2CMD_ENTITY_EXTRACTOR_MODE", None)
    else:
        os.environ["NLP2CMD_ENTITY_EXTRACTOR_MODE"] = mode

    if ab_ratio is None:
        os.environ.pop("NLP2CMD_ENTITY_AB_RATIO", None)
    else:
        os.environ["NLP2CMD_ENTITY_AB_RATIO"] = ab_ratio

    return {"mode": prev_mode, "ratio": prev_ratio}


def _restore_extractor_env(prev: dict[str, Optional[str]]) -> None:
    if prev.get("mode") is None:
        os.environ.pop("NLP2CMD_ENTITY_EXTRACTOR_MODE", None)
    else:
        os.environ["NLP2CMD_ENTITY_EXTRACTOR_MODE"] = str(prev["mode"])

    if prev.get("ratio") is None:
        os.environ.pop("NLP2CMD_ENTITY_AB_RATIO", None)
    else:
        os.environ["NLP2CMD_ENTITY_AB_RATIO"] = str(prev["ratio"])


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        default=str(_repo_root() / "tests" / "fixtures" / "entity_extraction_eval.json"),
    )
    parser.add_argument(
        "--mode",
        default="regex",
        choices=["regex", "semantic", "shadow", "ab"],
    )
    parser.add_argument("--ab-ratio", default=None)
    parser.add_argument("--only-diffs", action="store_true")
    parser.add_argument("--json-out", default=None)

    args = parser.parse_args(argv)

    _ensure_src_on_path()

    from nlp2cmd.generation.regex import RegexEntityExtractor
    from nlp2cmd.generation.semantic_entities import SemanticEntityExtractor

    dataset_path = Path(args.dataset)
    dataset = _load_dataset(dataset_path)

    regex_extractor = RegexEntityExtractor()

    prev_env = _set_extractor_env(args.mode, args.ab_ratio)
    try:
        semantic_extractor = SemanticEntityExtractor()
    finally:
        _restore_extractor_env(prev_env)

    rows: list[dict[str, Any]] = []
    total = 0
    diffs = 0

    for case in dataset:
        text = str(case.get("text", ""))
        domain = str(case.get("domain", ""))
        if not text or not domain:
            continue

        total += 1

        regex_entities = regex_extractor.extract(text, domain).entities

        prev = _set_extractor_env(args.mode, args.ab_ratio)
        try:
            semantic_result = semantic_extractor.extract(text, domain)
            semantic_entities = semantic_result.entities
            selected_mode = semantic_extractor.last_mode
            shadow_entities = semantic_extractor.last_semantic_entities
        finally:
            _restore_extractor_env(prev)

        delta = _diff_entities(regex_entities, semantic_entities)
        if delta:
            diffs += 1

        row = {
            "domain": domain,
            "text": text,
            "mode": args.mode,
            "selected_mode": selected_mode,
            "diff": delta,
            "regex": regex_entities,
            "semantic": semantic_entities,
            "shadow_entities": shadow_entities,
        }

        if not args.only_diffs or delta:
            rows.append(row)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        for row in rows:
            print(f"\n[{row['domain']}] {row['text']}")
            print(f"mode={row['mode']} selected={row['selected_mode']}")
            if row["diff"]:
                print("diff:")
                for k, v in row["diff"].items():
                    print(f"  {k}: regex={v['regex']} semantic={v['semantic']}")
            else:
                print("diff: <none>")

        print(f"\nSummary: cases={total} diffs={diffs}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
