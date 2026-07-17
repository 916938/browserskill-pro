"""
Unit tests for bsk_client module
"""

import sys
import os
import json
import unittest
from unittest.mock import patch, MagicMock, call

# Add skill/scripts to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skill', 'scripts'))

from bsk_client import bsk, bsk_with_raw, configure_utf8_output


class TestConfigureUtf8Output(unittest.TestCase):
    """Test UTF-8 output configuration."""

    def test_does_not_raise(self):
        """Should not raise any exception."""
        # Just verify it runs without errors
        configure_utf8_output()

    def test_callable(self):
        self.assertTrue(callable(configure_utf8_output))


class TestBskFunctionSuccess(unittest.TestCase):
    """Test bsk() function with successful responses."""

    @patch('bsk_client.subprocess.run')
    def test_json_response_parsed_correctly(self, mock_run):
        """Valid JSON response should be parsed and returned."""
        mock_run.return_value = MagicMock(
            stdout='{"tabs": [{"id": "1", "url": "https://example.com"}]}',
            returncode=0,
            stderr='',
        )

        result = bsk("tab list")

        self.assertIsInstance(result, dict)
        self.assertIn("tabs", result)
        self.assertEqual(len(result["tabs"]), 1)

    @patch('bsk_client.subprocess.run')
    def test_session_parameter_added(self, mock_run):
        """Session ID should be passed as --session flag."""
        mock_run.return_value = MagicMock(
            stdout='{}',
            returncode=0,
            stderr='',
        )

        bsk("tab list", session="abc123")

        # Check that --session was in the args
        args_call = mock_run.call_args[0][0]
        self.assertIn("--session", args_call)
        session_index = args_call.index("--session")
        self.assertEqual(args_call[session_index + 1], "abc123")

    @patch('bsk_client.subprocess.run')
    def test_positional_args_forwarded(self, mock_run):
        """Positional arguments should be appended to command."""
        mock_run.return_value = MagicMock(
            stdout='{"status": "ok"}',
            returncode=0,
            stderr='',
        )

        bsk("navigate", "https://example.com")

        args_call = mock_run.call_args[0][0]
        self.assertIn("navigate", args_call)
        self.assertIn("https://example.com", args_call)

    @patch('bsk_client.subprocess.run')
    def test_keyword_args_converted_to_flags(self, mock_run):
        """Keyword arguments converted to --key value format."""
        mock_run.return_value = MagicMock(
            stdout='{"clicked": true}',
            returncode=0,
            stderr='',
        )

        bsk("click", selector="#btn", timeout=30)

        args_call = mock_run.call_args[0][0]
        self.assertIn("--selector", args_call)
        self.assertIn("--timeout", args_call)

    @patch('bsk_client.subprocess.run')
    def test_json_flag_always_added(self, mock_run):
        """--json flag should always be present."""
        mock_run.return_value = MagicMock(
            stdout='{}',
            returncode=0,
            stderr='',
        )

        bsk("status")

        args_call = mock_run.call_args[0][0]
        self.assertIn("--json", args_call)

    @patch('bsk_client.subprocess.run')
    def test_command_split_into_args(self, mock_run):
        """String command should be split into arguments."""
        mock_run.return_value = MagicMock(
            stdout='{}',
            returncode=0,
            stderr='',
        )

        bsk("session start")

        args_call = mock_run.call_args[0][0]
        self.assertEqual(args_call[1], "session")
        self.assertEqual(args_call[2], "start")


class TestBskFunctionErrorHandling(unittest.TestCase):
    """Test bsk() function error scenarios."""

    @patch('bsk_client.subprocess.run')
    def test_error_in_json_response_raises_runtime_error(self, mock_run):
        """JSON response with 'error' key should raise RuntimeError."""
        mock_run.return_value = MagicMock(
            stdout='{"error": "daemon not running"}',
            returncode=0,
            stderr='',
        )

        with self.assertRaises(RuntimeError) as ctx:
            bsk("status")

        self.assertIn("daemon not running", str(ctx.exception))

    @patch('bsk_client.subprocess.run')
    def test_success_false_raises_runtime_error(self, mock_run):
        """Response with success=False should raise RuntimeError."""
        mock_run.return_value = MagicMock(
            stdout='{"success": false, "message": "failed"}',
            returncode=0,
            stderr='',
        )

        with self.assertRaises(RuntimeError):
            bsk("some-command")

    @patch('bsk_client.subprocess.run')
    def test_nonzero_exit_code_raises_runtime_error(self, mock_run):
        """Non-zero exit code should raise RuntimeError with stderr."""
        mock_run.return_value = MagicMock(
            stdout='',
            returncode=1,
            stderr='Invalid parameters',
        )

        with self.assertRaises(RuntimeError) as ctx:
            bsk("invalid-cmd")

        self.assertIn("Invalid parameters", str(ctx.exception))

    @patch('bsk_client.subprocess.run')
    def test_invalid_json_returns_none(self, mock_run):
        """Invalid JSON output (but success) should return None."""
        mock_run.return_value = MagicMock(
            stdout='not valid json',
            returncode=0,
            stderr='',
        )

        result = bsk("some-cmd")
        self.assertIsNone(result)


class TestBskWithRawFunction(unittest.TestCase):
    """Test bsk_with_raw() function."""

    @patch('bsk_client.subprocess.run')
    def test_returns_stdout_on_success(self, mock_run):
        """Should return raw stdout string."""
        expected_output = '{"raw": "output"}'
        mock_run.return_value = MagicMock(
            stdout=expected_output,
            returncode=0,
            stderr='',
        )

        result = bsk_with_raw("command")

        self.assertEqual(result, expected_output)

    @patch('bsk_client.subprocess.run')
    def test_session_param_works(self, mock_run):
        """Session parameter should work like in bsk()."""
        mock_run.return_value = MagicMock(
            stdout='data',
            returncode=0,
            stderr='',
        )

        bsk_with_raw("cmd", session="sess1")

        args_call = mock_run.call_args[0][0]
        self.assertIn("--session", args_call)

    @patch('bsk_client.subprocess.run')
    def test_nonzero_exit_code_raises(self, mock_run):
        """Non-zero exit code should raise RuntimeError."""
        mock_run.return_value = MagicMock(
            stdout='',
            returncode=2,
            stderr='Timeout occurred',
        )

        with self.assertRaises(RuntimeError) as ctx:
            bsk_with_raw("slow-cmd")

        self.assertIn("Timeout occurred", str(ctx.exception))

    @patch('bsk_client.subprocess.run')
    def test_no_json_flag_in_raw_mode(self, mock_run):
        """Raw mode should NOT add --json flag."""
        mock_run.return_value = MagicMock(
            stdout='plain text output',
            returncode=0,
            stderr='',
        )

        bsk_with_raw("status")

        args_call = mock_run.call_args[0][0]
        # Note: --json is only added by bsk(), not bsk_with_raw()
        self.assertNotIn("--json", args_call)

    @patch('bsk_client.subprocess.run')
    def test_kwargs_convert_to_flags(self, mock_run):
        """Kwargs should still convert to flags."""
        mock_run.return_value = MagicMock(
            stdout='result',
            returncode=0,
            stderr='',
        )

        bsk_with_raw("get", url="https://example.com")

        args_call = mock_run.call_args[0][0]
        self.assertIn("--url", args_call)


class TestSubprocessIntegration(unittest.TestCase):
    """Test subprocess interaction details."""

    @patch('bsk_client.subprocess.run')
    def test_uses_capture_output(self, mock_run):
        """Should capture both stdout and stderr."""
        mock_run.return_value = MagicMock(stdout='', returncode=0, stderr='')

        bsk("test")

        kwargs = mock_run.call_args[1]
        self.assertTrue(kwargs.get('capture_output'))

    @patch('bsk_client.subprocess.run')
    def test_uses_text_mode(self, mock_run):
        """Should use text mode for string output."""
        mock_run.return_value = MagicMock(stdout='', returncode=0, stderr='')

        bsk("test")

        kwargs = mock_run.call_args[1]
        self.assertTrue(kwargs.get('text'))

    @patch('bsk_client.subprocess.run')
    def test_specifies_utf8_encoding(self, mock_run):
        """Should specify UTF-8 encoding."""
        mock_run.return_value = MagicMock(stdout='', returncode=0, stderr='')

        bsk("test")

        kwargs = mock_run.call_args[1]
        self.assertEqual(kwargs.get('encoding'), 'utf-8')

    @patch('bsk_client.subprocess.run')
    def test_handles_encoding_errors(self, mock_run):
        """Should handle encoding errors gracefully."""
        mock_run.return_value = MagicMock(
            stdout='',
            returncode=0,
            stderr='',
        )

        bsk("test")

        kwargs = mock_run.call_args[1]
        self.assertEqual(kwargs.get('errors'), 'replace')


class TestEdgeCases(unittest.TestCase):
    """Edge case tests for bsk_client."""

    @patch('bsk_client.subprocess.run')
    def test_empty_command(self, mock_run):
        """Empty command should still call subprocess."""
        mock_run.return_value = MagicMock(stdout='{}', returncode=0, stderr='')

        result = bsk("")
        self.assertIsNotNone(result)

    @patch('bsk_client.subprocess.run')
    def test_complex_nested_json(self, mock_run):
        """Should handle complex nested JSON structures."""
        complex_data = {
            "level1": {
                "level2": {
                    "items": [1, 2, 3],
                    "metadata": {"count": 3}
                }
            }
        }
        mock_run.return_value = MagicMock(
            stdout=json.dumps(complex_data),
            returncode=0,
            stderr='',
        )

        result = bsk("complex")

        self.assertEqual(result["level1"]["level2"]["items"], [1, 2, 3])

    @patch('bsk_client.subprocess.run')
    def test_unicode_in_output(self, mock_run):
        """Should handle Unicode characters correctly."""
        unicode_output = '{"message": "中文测试 🎉"}'
        mock_run.return_value = MagicMock(
            stdout=unicode_output,
            returncode=0,
            stderr='',
        )

        result = bsk("unicode-test")
        self.assertIn("中文测试", result["message"])

    @patch('bsk_client.subprocess.run')
    def test_large_output(self, mock_run):
        """Should handle large JSON outputs."""
        large_list = list(range(10000))
        mock_run.return_value = MagicMock(
            stdout=json.dumps({"data": large_list}),
            returncode=0,
            stderr='',
        )

        result = bsk("large-data")
        self.assertEqual(len(result["data"]), 10000)


class TestBsWithMultipleCalls(unittest.TestCase):
    """Test multiple sequential calls."""

    @patch('bsk_client.subprocess.run')
    def test_sequential_calls_independent(self, mock_run):
        """Multiple calls should be independent."""
        responses = [
            '{"session": "sess1"}',
            '{"tabs": []}',
            '{"result": "ok"}',
        ]
        mock_run.side_effect = [
            MagicMock(stdout=r, returncode=0, stderr='') for r in responses
        ]

        r1 = bsk("session start")
        r2 = bsk("tab list")
        r3 = bsk("some action")

        self.assertEqual(r1["session"], "sess1")
        self.assertEqual(r2["tabs"], [])
        self.assertEqual(r3["result"], "ok")
        self.assertEqual(mock_run.call_count, 3)


if __name__ == "__main__":
    unittest.main()
