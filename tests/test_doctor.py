import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).parents[1] / "skill" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import doctor  # noqa: E402


class DoctorTests(unittest.TestCase):
    def test_parse_doctor_output_accepts_json(self):
        checks, error = doctor.parse_doctor_output(
            '[{"ok":true,"reason":"daemon running"},{"ok":true,"reason":"extension connected"}]'
        )

        self.assertIsNone(error)
        self.assertEqual(len(checks), 2)

    def test_parse_doctor_output_reports_invalid_json(self):
        checks, error = doctor.parse_doctor_output("not json")

        self.assertIsNone(checks)
        self.assertIn("invalid doctor JSON", error)

    def test_report_ready_requires_all_checks_ok(self):
        report = {
            "checks": [
                {"ok": True, "reason": "daemon running"},
                {"ok": True, "reason": "extension connected"},
            ],
        }

        self.assertTrue(doctor.report_ready(report))

    def test_report_ready_fails_when_check_fails(self):
        report = {
            "checks": [
                {"ok": True, "reason": "daemon running"},
                {"ok": False, "reason": "extension not connected"},
            ],
        }

        self.assertFalse(doctor.report_ready(report))

    def test_readiness_reason_reports_ready(self):
        report = {
            "checks": [
                {"ok": True, "reason": "daemon running"},
                {"ok": True, "reason": "extension connected"},
            ],
        }

        self.assertEqual(doctor.readiness_reason(report), "ready")

    def test_readiness_reason_reports_failed_check(self):
        report = {
            "checks": [
                {"ok": True, "reason": "daemon running"},
                {"ok": False, "reason": "extension not connected"},
            ],
        }

        self.assertIn("extension not connected", doctor.readiness_reason(report))

    def test_json_flag_is_accepted(self):
        with patch.object(sys, "argv", ["doctor.py", "--json"]):
            args = doctor.parse_args()

        self.assertTrue(args.json)

    def test_sleep_until_deadline_clamps_to_remaining_time(self):
        with patch.object(doctor.time, "monotonic", return_value=3.0):
            with patch.object(doctor.time, "sleep") as sleep:
                self.assertTrue(doctor.sleep_until_deadline(5.0, 10.0))

        sleep.assert_called_once_with(2.0)

    def test_sleep_until_deadline_skips_elapsed_deadline(self):
        with patch.object(doctor.time, "monotonic", return_value=5.0):
            with patch.object(doctor.time, "sleep") as sleep:
                self.assertFalse(doctor.sleep_until_deadline(5.0, 10.0))

        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()