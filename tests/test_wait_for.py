import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).parents[1] / "skill" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import wait_for  # noqa: E402


class WaitForArgumentTests(unittest.TestCase):
    def test_visible_text_alias_maps_to_text_contains(self):
        with patch.object(
            sys,
            "argv",
            ["wait_for.py", "--session", "demo", "--visible-text", "Ready"],
        ):
            args = wait_for.parse_args()

        self.assertEqual(args.text_contains, "Ready")

    def test_iter_names_handles_deep_trees_iteratively(self):
        tree = {"name": "deep leaf"}
        for _ in range(3000):
            tree = {"children": [tree]}

        self.assertEqual(list(wait_for.iter_names(tree)), ["deep leaf"])

    def test_sleep_until_deadline_clamps_to_remaining_time(self):
        with patch.object(wait_for.time, "monotonic", return_value=3.0):
            with patch.object(wait_for.time, "sleep") as sleep:
                self.assertTrue(wait_for.sleep_until_deadline(5.0, 10.0))

        sleep.assert_called_once_with(2.0)

    def test_main_does_not_poll_after_deadline_sleep(self):
        with patch.object(
            sys,
            "argv",
            [
                "wait_for.py",
                "--session",
                "demo",
                "--text-contains",
                "Ready",
                "--timeout",
                "1",
                "--interval",
                "10",
            ],
        ):
            with patch.object(wait_for, "configure_utf8_output"):
                with patch.object(
                    wait_for.time,
                    "monotonic",
                    side_effect=[0.0, 0.0, 0.0, 1.01, 1.01],
                ):
                    with patch.object(wait_for.time, "sleep") as sleep:
                        with patch.object(
                            wait_for,
                            "bsk",
                            return_value={
                                "data": {
                                    "url": "https://example.test",
                                    "title": "Example",
                                    "tree": {"name": "Not ready"},
                                }
                            },
                        ) as bsk_mock:
                            with redirect_stdout(StringIO()):
                                with self.assertRaises(SystemExit) as raised:
                                    wait_for.main()

        self.assertEqual(raised.exception.code, 1)
        bsk_mock.assert_called_once()
        sleep.assert_called_once_with(1.0)


if __name__ == "__main__":
    unittest.main()