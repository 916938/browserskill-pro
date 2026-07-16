#!/usr/bin/env python3

import argparse
import json
import time

from bsk_client import configure_utf8_output, bsk


def parse_args():
    parser = argparse.ArgumentParser(
        description="Poll the selected BrowserSkill tab until a page condition matches."
    )
    parser.add_argument("--session", help="BrowserSkill session ID")
    parser.add_argument("--url-contains")
    parser.add_argument("--title-contains")
    parser.add_argument(
        "--text-contains",
        "--visible-text",
        dest="text_contains",
        help="Wait until accessible text contains this value.",
    )
    parser.add_argument("--timeout", type=float, default=10)
    parser.add_argument("--interval", type=float, default=1)
    return parser.parse_args()


def iter_names(nodes):
    stack = [nodes]
    while stack:
        current = stack.pop()
        if isinstance(current, list):
            stack.extend(reversed(current))
        elif isinstance(current, dict):
            name = current.get("name")
            if name:
                yield str(name)
            children = current.get("children")
            if children is not None:
                stack.append(children)


def matches(args, data):
    url = data.get("url") or ""
    title = data.get("title") or ""
    if args.url_contains and args.url_contains not in url:
        return False
    if args.title_contains and args.title_contains not in title:
        return False
    if args.text_contains:
        text = "\n".join(iter_names(data.get("tree")))
        if args.text_contains not in text:
            return False
    return True


def sleep_until_deadline(deadline, interval):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return False
    time.sleep(min(interval, remaining))
    return True


def main():
    configure_utf8_output()
    args = parse_args()
    if not any((args.url_contains, args.title_contains, args.text_contains)):
        raise SystemExit("Specify at least one URL, title, or text condition.")
    if args.timeout <= 0 or args.interval <= 0:
        raise SystemExit("--timeout and --interval must be positive.")

    deadline = time.monotonic() + args.timeout
    last_data = {}
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        try:
            response = bsk("snapshot", args.session)
        except RuntimeError as error:
            raise SystemExit(str(error)) from error

        last_data = response.get("data") or {}
        if matches(args, last_data):
            print(
                json.dumps(
                    {
                        "matched": True,
                        "url": last_data.get("url"),
                        "title": last_data.get("title"),
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
            return
        if not sleep_until_deadline(deadline, args.interval):
            break

    print(
        json.dumps(
            {
                "matched": False,
                "url": last_data.get("url"),
                "title": last_data.get("title"),
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()