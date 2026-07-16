#!/usr/bin/env python3

import argparse
import json
import subprocess
import time

from bsk_client import configure_utf8_output


def run_bsk_doctor():
    result = subprocess.run(
        ["bsk", "doctor", "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def parse_doctor_output(stdout):
    text = stdout.strip()
    if not text:
        return None, "empty doctor output"
    try:
        return json.loads(text), None
    except json.JSONDecodeError as error:
        return None, f"invalid doctor JSON: {error}"


def status_snapshot():
    command_result = run_bsk_doctor()
    checks = None
    error = None
    if command_result["returncode"] == 0:
        checks, error = parse_doctor_output(command_result["stdout"])
    else:
        error = command_result["stderr"] or command_result["stdout"]

    return {
        "command_returncode": command_result["returncode"],
        "checks": checks,
        "error": error,
    }


def report_ready(report):
    checks = report.get("checks") or []
    return all(check.get("ok", False) for check in checks)


def readiness_reason(report):
    checks = report.get("checks") or []
    if not checks:
        return report.get("error") or "bsk doctor unavailable"

    failed_checks = [check for check in checks if not check.get("ok", False)]
    if failed_checks:
        return "; ".join(failed_checks[0].get("reason", "unknown") for _ in failed_checks[:3])

    return "ready"


def sleep_until_deadline(deadline, interval):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return False
    time.sleep(min(interval, remaining))
    return True


def wait_for_ready(timeout, interval):
    deadline = time.monotonic() + timeout
    last = status_snapshot()
    while True:
        if report_ready(last):
            return last
        if not sleep_until_deadline(deadline, interval):
            break
        last = status_snapshot()
    return last


def build_recommendations(report):
    recommendations = []
    checks = report.get("checks") or []

    if not checks:
        recommendations.append("Run 'bsk doctor' to diagnose readiness.")
        return recommendations

    for check in checks:
        if not check.get("ok", False):
            reason = check.get("reason", "")
            if "extension" in reason.lower():
                recommendations.append("Install and enable the BrowserSkill browser extension.")
            elif "daemon" in reason.lower():
                recommendations.append("Start the BrowserSkill daemon with 'bsk daemon start'.")
            elif "browser" in reason.lower():
                recommendations.append("Open Chrome or Edge browser.")
            else:
                recommendations.append(f"Fix: {reason}")

    if report_ready(report):
        recommendations.append(
            "Ready: bsk daemon is running, the browser extension is connected."
        )

    return recommendations


def parse_args():
    parser = argparse.ArgumentParser(
        description="Diagnose local BrowserSkill readiness without sending browser actions."
    )
    parser.add_argument("--wait-connected", type=float, default=0)
    parser.add_argument("--interval", type=float, default=2)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Compatibility flag; doctor output is always JSON.",
    )
    return parser.parse_args()


def main():
    configure_utf8_output()
    args = parse_args()
    if args.wait_connected < 0 or args.interval <= 0:
        raise SystemExit("--wait-connected must be non-negative and --interval must be positive.")

    report = status_snapshot()

    if args.wait_connected:
        report = wait_for_ready(
            timeout=args.wait_connected,
            interval=args.interval,
        )

    report["ready"] = report_ready(report)
    report["reason"] = readiness_reason(report)
    report["recommendations"] = build_recommendations(report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["ready"] else 1)


if __name__ == "__main__":
    main()