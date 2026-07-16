import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).parents[1] / "skill" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from snapshot import auto_snapshot, compact_snapshot, parse_args  # noqa: E402


class CompactSnapshotTests(unittest.TestCase):
    def test_compact_snapshot_does_not_enqueue_large_flat_lists(self):
        class CountingList(list):
            def __init__(self, *args):
                super().__init__(*args)
                self.iterated = 0
                self.reversed = 0

            def __iter__(self):
                for item in super().__iter__():
                    self.iterated += 1
                    yield item

            def __reversed__(self):
                for item in super().__reversed__():
                    self.reversed += 1
                    yield item

        children = CountingList(
            {"role": "link", "name": f"Item {index}", "ref": f"@e{index}"}
            for index in range(1000)
        )
        response = {"ok": True, "data": {"tree": children}}

        result = compact_snapshot(response, max_elements=1, max_name_length=240)

        self.assertEqual(len(result["elements"]), 1)
        self.assertTrue(result["truncated"])
        self.assertEqual(children.iterated, 1)
        self.assertEqual(children.reversed, 0)

    def test_nested_lists_are_flattened(self):
        response = {
            "ok": True,
            "data": {
                "url": "https://example.com",
                "title": "Example",
                "tree": [
                    [
                        {"role": "link", "name": "First", "ref": "@e1"},
                        {"role": "button", "name": "Second", "ref": "@e2"},
                    ],
                    [{"role": "heading", "name": "Nested heading"}],
                ],
            },
        }

        result = compact_snapshot(response, max_elements=10, max_name_length=240)

        self.assertEqual(
            [item["role"] for item in result["elements"]],
            ["link", "button", "heading"],
        )
        self.assertEqual(result["elements"][0]["ref"], "@e1")
        self.assertEqual(result["elements"][0]["usage"], "click selector @e1")
        self.assertFalse(result["truncated"])

    def test_non_mapping_children_are_ignored(self):
        response = {
            "ok": True,
            "data": {
                "tree": [
                    None,
                    "unexpected",
                    {"role": "heading", "name": "Still works", "children": [42]},
                ]
            },
        }

        result = compact_snapshot(response, max_elements=10, max_name_length=240)

        self.assertEqual(result["elements"], [{"role": "heading", "name": "Still works"}])

    def test_max_elements_sets_truncated(self):
        response = {
            "ok": True,
            "data": {
                "tree": [
                    {"role": "link", "name": "One", "ref": "@e1"},
                    {"role": "link", "name": "Two", "ref": "@e2"},
                ]
            },
        }

        result = compact_snapshot(response, max_elements=1, max_name_length=240)

        self.assertEqual(len(result["elements"]), 1)
        self.assertTrue(result["truncated"])

    def test_compact_snapshot_handles_deep_trees_iteratively(self):
        tree = {"role": "heading", "name": "deep leaf"}
        for _ in range(3000):
            tree = {"role": "generic", "children": [tree]}

        result = compact_snapshot(
            {
                "ok": True,
                "data": {
                    "url": "https://example.com",
                    "title": "Deep",
                    "tree": tree,
                },
            },
            max_elements=10,
            max_name_length=240,
        )

        self.assertEqual(result["elements"], [{"role": "heading", "name": "deep leaf"}])

    def test_auto_mode_returns_compact_for_small_snapshots(self):
        response = {
            "ok": True,
            "data": {
                "url": "https://example.com",
                "title": "Example",
                "tree": [{"role": "link", "name": "Read", "ref": "@e1"}],
            },
        }
        args = type(
            "Args",
            (),
            {
                "max_elements": 10,
                "max_name_length": 240,
                "auto_file_bytes": 10000,
                "output": None,
            },
        )()

        result = auto_snapshot(response, args)

        self.assertEqual(result["mode"], "compact")
        self.assertEqual(result["elements"][0]["usage"], "click selector @e1")
        self.assertIn("snapshot_bytes", result)

    def test_auto_mode_writes_file_when_snapshot_is_large(self):
        response = {
            "ok": True,
            "data": {
                "url": "https://example.com",
                "title": "Example",
                "tree": [{"role": "heading", "name": "A" * 200}],
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "snapshot.json"
            args = type(
                "Args",
                (),
                {
                    "max_elements": 10,
                    "max_name_length": 240,
                    "auto_file_bytes": 1,
                    "output": output,
                },
            )()

            result = auto_snapshot(response, args)

            self.assertEqual(result["mode"], "file")
            self.assertEqual(Path(result["path"]), output.resolve())
            self.assertTrue(output.exists())
            self.assertEqual(result["reason"], "raw snapshot exceeds auto-file-bytes")

    def test_auto_flag_sets_mode(self):
        with patch.object(sys, "argv", ["snapshot.py", "--auto"]):
            args = parse_args()

        self.assertEqual(args.mode, "auto")


if __name__ == "__main__":
    unittest.main()
