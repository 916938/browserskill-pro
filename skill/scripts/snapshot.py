#!/usr/bin/env python3

import argparse
import json
import tempfile
from pathlib import Path

from bsk_client import configure_utf8_output, bsk


def parse_args():
    parser = argparse.ArgumentParser(
        description="Capture a BrowserSkill snapshot without flooding agent context."
    )
    parser.add_argument("--session", help="BrowserSkill session ID")
    parser.add_argument(
        "--mode",
        choices=("auto", "compact", "file", "full"),
        default="compact",
        help="auto strategy, compact summary, file path, or full JSON output",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Shortcut for --mode auto.",
    )
    parser.add_argument("--output", type=Path, help="Path used by file mode")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--max-elements", type=int, default=250)
    parser.add_argument("--max-name-length", type=int, default=240)
    parser.add_argument(
        "--auto-file-bytes",
        type=int,
        default=120000,
        help="Auto mode writes a file when the raw snapshot is at least this large.",
    )
    args = parser.parse_args()
    if args.auto:
        args.mode = "auto"
    return args


def request_snapshot(args):
    try:
        return bsk("snapshot", args.session)
    except RuntimeError as error:
        raise SystemExit(str(error)) from error


def compact_snapshot(response, max_elements, max_name_length):
    data = response.get("data") or {}
    elements = []

    stack = [iter([data.get("tree")])]
    while stack and len(elements) < max_elements:
        try:
            nodes = next(stack[-1])
        except StopIteration:
            stack.pop()
            continue
        if isinstance(nodes, list):
            stack.append(iter(nodes))
            continue
        if not isinstance(nodes, dict):
            continue

        role = nodes.get("role")
        ref = nodes.get("ref")
        name = nodes.get("name")
        if ref or role in {"heading", "button", "link", "textbox", "combobox"}:
            item = {"role": role}
            if name:
                item["name"] = str(name)[:max_name_length]
            if ref:
                item["ref"] = ref
                if role in {"textbox", "combobox"}:
                    item["usage"] = f"fill selector {ref}"
                elif role in {"button", "link"}:
                    item["usage"] = f"click selector {ref}"
                else:
                    item["usage"] = f"use selector {ref} with click or fill"
            elements.append(item)
        children = nodes.get("children")
        if children is not None:
            stack.append(iter(children if isinstance(children, list) else [children]))
    return {
        "ok": response.get("ok"),
        "url": data.get("url"),
        "title": data.get("title"),
        "elements": elements,
        "truncated": len(elements) >= max_elements,
    }


def write_snapshot(response, output):
    if output is None:
        directory = Path(tempfile.gettempdir()) / "browserskill-snapshots"
        directory.mkdir(parents=True, exist_ok=True)
        handle = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".json",
            prefix="snapshot_",
            dir=directory,
            delete=False,
        )
        output = Path(handle.name)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        handle = output.open("w", encoding="utf-8")

    with handle:
        json.dump(response, handle, ensure_ascii=False, separators=(",", ":"))
    return output.resolve()


def snapshot_size_bytes(response):
    return len(json.dumps(response, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def auto_snapshot(response, args):
    raw_bytes = snapshot_size_bytes(response)
    compact = compact_snapshot(
        response,
        max_elements=args.max_elements,
        max_name_length=args.max_name_length,
    )
    should_write_file = raw_bytes >= args.auto_file_bytes or compact["truncated"]
    if not should_write_file:
        compact["mode"] = "compact"
        compact["snapshot_bytes"] = raw_bytes
        return compact

    path = write_snapshot(response, args.output)
    return {
        "ok": response.get("ok"),
        "mode": "file",
        "path": str(path),
        "url": (response.get("data") or {}).get("url"),
        "title": (response.get("data") or {}).get("title"),
        "snapshot_bytes": raw_bytes,
        "reason": (
            "compact summary reached max-elements"
            if compact["truncated"]
            else "raw snapshot exceeds auto-file-bytes"
        ),
        "compact_preview": compact,
    }


def main():
    configure_utf8_output()
    args = parse_args()
    response = request_snapshot(args)

    if args.mode == "auto":
        result = auto_snapshot(response, args)
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    elif args.mode == "file":
        print(write_snapshot(response, args.output))
    elif args.mode == "full":
        print(json.dumps(response, ensure_ascii=False, separators=(",", ":")))
    else:
        result = compact_snapshot(
            response,
            max_elements=args.max_elements,
            max_name_length=args.max_name_length,
        )
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()