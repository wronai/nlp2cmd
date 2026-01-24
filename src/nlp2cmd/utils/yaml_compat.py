"""Internal YAML compatibility layer.

This project depends on PyYAML at runtime, but some minimal environments used for
running tests may not have it installed. This module provides a small fallback
implementation for a limited YAML subset used in tests.

Do not import PyYAML directly from other modules; instead use:

    from nlp2cmd.utils.yaml_compat import yaml

"""

from __future__ import annotations

from typing import Any, Optional


try:
    import yaml as _yaml  # type: ignore
except Exception:  # pragma: no cover

    class YAMLError(Exception):
        pass

    def _parse_scalar(text: str) -> Any:
        t = text.strip()
        if t == "":
            return ""
        if t.lower() in {"true", "yes", "on"}:
            return True
        if t.lower() in {"false", "no", "off"}:
            return False
        if t.lower() in {"null", "none", "~"}:
            return None
        if (t.startswith("\"") and t.endswith("\"")) or (t.startswith("'") and t.endswith("'")):
            return t[1:-1]
        try:
            if "." in t:
                return float(t)
            return int(t)
        except Exception:
            return t

    class _Frame:
        def __init__(self, indent: int, container: Any, parent: Any = None, parent_key: Optional[str] = None):
            self.indent = indent
            self.container = container
            self.parent = parent
            self.parent_key = parent_key

    def safe_load(stream: str) -> Any:  # noqa: D401
        """Parse a minimal subset of YAML into Python objects."""
        if stream is None:
            return None
        lines = str(stream).splitlines()
        # Remove comments / empty lines
        cleaned: list[tuple[int, str]] = []
        for raw in lines:
            if not raw.strip():
                continue
            stripped = raw.lstrip(" ")
            if stripped.startswith("#"):
                continue
            indent = len(raw) - len(stripped)
            cleaned.append((indent, stripped.rstrip()))

        if not cleaned:
            return None

        root: Any = {}
        stack: list[_Frame] = [_Frame(indent=0, container=root, parent=None, parent_key=None)]

        for indent, content in cleaned:
            while stack and indent < stack[-1].indent:
                stack.pop()
            if not stack:
                stack = [_Frame(indent=0, container=root, parent=None, parent_key=None)]

            frame = stack[-1]
            current = frame.container

            is_list_item = content.startswith("- ")

            # If we're about to add list items but container is an empty dict placeholder, convert.
            if is_list_item and isinstance(current, dict) and frame.parent is not None and frame.parent_key is not None:
                if current == {} and isinstance(frame.parent, dict) and frame.parent.get(frame.parent_key) is current:
                    new_list: list[Any] = []
                    frame.parent[frame.parent_key] = new_list
                    frame.container = new_list
                    current = new_list

            if is_list_item:
                if not isinstance(current, list):
                    raise YAMLError("Invalid YAML structure: list item in non-list container")

                item_text = content[2:].strip()
                if ":" in item_text:
                    key, val = item_text.split(":", 1)
                    key = key.strip()
                    val = val.strip()
                    item_dict: dict[str, Any] = {}
                    if val == "":
                        item_dict[key] = {}
                        current.append(item_dict)
                        stack.append(_Frame(indent=indent + 2, container=item_dict, parent=None, parent_key=None))
                        stack.append(_Frame(indent=indent + 4, container=item_dict[key], parent=item_dict, parent_key=key))
                    else:
                        item_dict[key] = _parse_scalar(val)
                        current.append(item_dict)
                        stack.append(_Frame(indent=indent + 2, container=item_dict, parent=None, parent_key=None))
                else:
                    current.append(_parse_scalar(item_text))
                continue

            if ":" not in content:
                raise YAMLError(f"Invalid YAML line: {content}")

            key, val = content.split(":", 1)
            key = key.strip()
            val = val.strip()

            if not isinstance(current, dict):
                raise YAMLError("Invalid YAML structure: mapping entry in non-mapping container")

            if val == "":
                placeholder: dict[str, Any] = {}
                current[key] = placeholder
                stack.append(_Frame(indent=indent + 2, container=placeholder, parent=current, parent_key=key))
            else:
                current[key] = _parse_scalar(val)

        return root

    def load(stream: str, Loader: Any = None) -> Any:  # noqa: N803
        return safe_load(stream)

    def _dump_obj(obj: Any, indent: int) -> str:
        pad = " " * indent
        if isinstance(obj, dict):
            out_lines: list[str] = []
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    out_lines.append(f"{pad}{k}:")
                    out_lines.append(_dump_obj(v, indent + 2))
                else:
                    out_lines.append(f"{pad}{k}: {v}")
            return "\n".join(out_lines)
        if isinstance(obj, list):
            out_lines = []
            for item in obj:
                if isinstance(item, (dict, list)):
                    out_lines.append(f"{pad}-")
                    out_lines.append(_dump_obj(item, indent + 2))
                else:
                    out_lines.append(f"{pad}- {item}")
            return "\n".join(out_lines)
        return f"{pad}{obj}"

    def dump(data: Any, default_flow_style: bool = False, sort_keys: bool = False, **_: Any) -> str:
        return _dump_obj(data, indent=0) + "\n"

    def safe_dump(data: Any, sort_keys: bool = False, allow_unicode: bool = True, **kwargs: Any) -> str:
        return dump(data, sort_keys=sort_keys, **kwargs)

    class _YamlCompat:
        safe_load = staticmethod(safe_load)
        load = staticmethod(load)
        dump = staticmethod(dump)
        safe_dump = staticmethod(safe_dump)
        YAMLError = YAMLError

    yaml = _YamlCompat()

else:  # pragma: no cover
    yaml = _yaml
