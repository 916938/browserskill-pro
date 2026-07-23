#!/usr/bin/env python3
"""Replay a `bsk record` trace.json by driving the corresponding bsk tools.

Reads a Trace v2 (per bsk-protocol/tools/record.rs), takes a fresh snapshot
before each interactive step, matches each step's TargetDescriptor to an
@eN ref, and issues the equivalent bsk command (navigate / click / fill /
select / press).

Design red lines:
- redacted:true fill steps STOP replay and defer to the user; passwords must
  never be typed as literal "***" or similar placeholders.
- Steps that fail to match a target are HARD ERRORS. Do not brute-force.
- --dry-run prints the resolved commands without touching bsk. Use it first.
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from bsk_client import bsk, configure_utf8_output


# ---------- Snapshot text parser ----------
# Format examples (indent = ancestry, one node per line):
#   RootWebArea "Example"
#     @e1 heading "Example Domain"
#     @e2 button "Submit"
# The leading `@eN` marker is present only for elements that were assigned a
# ref; heading / staticText etc. may appear without one. We only need refs.

REF_LINE = re.compile(
    r'^(?P<indent>\s*)@(?P<ref>e\d+)\s+(?P<role>\S+)(?:\s+"(?P<name>[^"]*)")?'
)


@dataclass(frozen=True)
class SnapshotRef:
    ref: str
    role: str
    name: str  # empty string when absent


def parse_snapshot_text(text: str) -> list[SnapshotRef]:
    refs: list[SnapshotRef] = []
    for line in text.splitlines():
        m = REF_LINE.match(line)
        if m:
            refs.append(
                SnapshotRef(
                    ref=f"@{m.group('ref')}",
                    role=m.group("role"),
                    name=m.group("name") or "",
                )
            )
    return refs


# ---------- Target matcher ----------

def match_target(target: dict, refs: list[SnapshotRef]) -> SnapshotRef:
    """Pick the ref that best matches a trace TargetDescriptor.

    Trace target fields: role, name, tag, name_attr, placeholder, nearby_label.
    Snapshot refs only carry role + name, so matching is best-effort on those two.
    Raises ValueError when there is no unambiguous match — the caller must not
    guess or fall back to arbitrary refs.
    """
    want_role = (target.get("role") or "").strip()
    want_name = (target.get("name") or "").strip()

    def score(r: SnapshotRef) -> int:
        # A ref must satisfy every non-empty target field, else it does not
        # qualify. Otherwise a target with a mismatched name would silently
        # return a same-role ref just because the role happened to be unique.
        if want_role and r.role != want_role:
            return 0
        name_score = 0
        if want_name:
            if r.name == want_name:
                name_score = 20
            elif r.name.startswith(want_name):
                name_score = 5
            elif want_name in r.name:
                name_score = 3
            else:
                return 0  # name required but no match at all
        return (10 if want_role else 0) + name_score

    scored = [(score(r), r) for r in refs]
    scored = [(s, r) for s, r in scored if s > 0]
    if not scored:
        raise ValueError(
            f"no ref matches target role={want_role!r} name={want_name!r}"
        )
    scored.sort(key=lambda x: x[0], reverse=True)
    top_score = scored[0][0]
    top = [r for s, r in scored if s == top_score]
    if len(top) > 1:
        raise ValueError(
            f"ambiguous target role={want_role!r} name={want_name!r}: "
            f"{len(top)} equally-scoring refs {[r.ref for r in top]}"
        )
    return top[0]


# ---------- Step execution ----------

class ReplayError(RuntimeError):
    pass


def snapshot_refs(session: str) -> list[SnapshotRef]:
    result = bsk("snapshot", session)
    if not isinstance(result, dict) or "text" not in result:
        raise ReplayError(f"unexpected snapshot response shape: {result!r}")
    return parse_snapshot_text(result["text"])


def dispatch_step(step: dict, session: str, dry_run: bool) -> None:
    op = step.get("op")
    step_id = step.get("id", "?")
    prefix = f"step {step_id} ({op})"

    if op == "navigate":
        url = step["to"]
        print(f"{prefix}: navigate {url}")
        if not dry_run:
            bsk("navigate", session, url)
        return

    if op == "press":
        key = step["key"]
        modifiers = step.get("modifiers") or []
        target = step.get("target")
        kwargs = {}
        if modifiers:
            kwargs["modifiers"] = ",".join(modifiers)
        if target:
            refs = snapshot_refs(session)
            ref = match_target(target, refs)
            kwargs["ref"] = ref.ref
            print(f"{prefix}: press {key} (mods={modifiers}) on {ref.ref} {ref.role} {ref.name!r}")
        else:
            print(f"{prefix}: press {key} (mods={modifiers})")
        if not dry_run:
            bsk("press", session, key, **kwargs)
        return

    if op == "fill":
        if step.get("redacted"):
            raise ReplayError(
                f"{prefix}: value is redacted; a human must supply the real value. "
                f"Halting replay — do not type the placeholder."
            )
        refs = snapshot_refs(session)
        ref = match_target(step["target"], refs)
        value = step["value"]
        print(f"{prefix}: fill {ref.ref} = {value!r}")
        if not dry_run:
            bsk("fill", session, ref.ref, value=value)
        return

    if op == "click":
        refs = snapshot_refs(session)
        ref = match_target(step["target"], refs)
        print(f"{prefix}: click {ref.ref} {ref.role} {ref.name!r}")
        if not dry_run:
            bsk("click", session, ref.ref)
        # navigated_to → wait for the page to settle before the next step.
        if step.get("effect", {}).get("navigated_to"):
            print(f"{prefix}: waiting for navigation")
            if not dry_run:
                # 'load' is the default; keep it explicit for clarity.
                bsk("wait-for-navigation", session, **{"wait-until": "load"})
        return

    if op == "select":
        refs = snapshot_refs(session)
        ref = match_target(step["target"], refs)
        # `bsk select` takes repeated --value; bsk_client's kwargs helper only
        # supports one value per flag, so shell out with a manual list.
        values = [opt["value"] for opt in step["selection"]]
        print(f"{prefix}: select {ref.ref} values={values}")
        if dry_run:
            return
        # bsk_client.bsk doesn't support repeated flags; construct manually.
        import subprocess
        args = ["bsk", "select", ref.ref, "--session", session]
        for v in values:
            args += ["--value", v]
        args.append("--json")
        r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            raise ReplayError(f"{prefix}: bsk select failed: {r.stderr.strip()}")
        return

    raise ReplayError(f"{prefix}: unknown op {op!r}")


# ---------- CLI ----------

def parse_args():
    p = argparse.ArgumentParser(
        description="Replay a bsk record trace against a live session."
    )
    p.add_argument("trace", type=Path, help="Path to trace.json from bsk record")
    p.add_argument("--session", required=True, help="Active bsk session id")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print resolved commands without executing them",
    )
    p.add_argument(
        "--from-step",
        type=int,
        default=None,
        help="Skip steps with id < this (useful when resuming after a failure)",
    )
    return p.parse_args()


def main():
    configure_utf8_output()
    args = parse_args()
    try:
        trace = json.loads(args.trace.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read trace {args.trace}: {exc}", file=sys.stderr)
        sys.exit(2)

    steps = trace.get("steps") or []
    if not steps:
        print("error: trace has no steps", file=sys.stderr)
        sys.exit(2)

    if trace.get("purpose"):
        print(f"purpose: {trace['purpose']}")
    print(f"entry: {trace.get('entry', {}).get('start_url', '?')}")
    print(f"steps: {len(steps)} (dry-run={args.dry_run})")

    for step in steps:
        if args.from_step is not None and step.get("id", 0) < args.from_step:
            continue
        try:
            dispatch_step(step, args.session, args.dry_run)
        except (ReplayError, ValueError, RuntimeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            print(
                f"replay halted at step {step.get('id')}; "
                f"resume with --from-step {step.get('id')}",
                file=sys.stderr,
            )
            sys.exit(1)

    print("replay complete")


if __name__ == "__main__":
    main()
