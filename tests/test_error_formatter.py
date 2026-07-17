"""
Unit tests for error_formatter module
"""

import json
import sys
import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

# Add skill/scripts to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skill', 'scripts'))

from error_codes import TIMEOUT, INVALID_PARAMS, DAEMON_CRASHED
from error_formatter import (
    ErrorResponseBuilder,
    SUGGESTION_MAP,
    RECOVERY_MAP,
    build_error_response,
    build_success_response,
)


class TestErrorResponseBuilder(unittest.TestCase):
    """Test ErrorResponseBuilder class."""

    def setUp(self):
        self.builder = ErrorResponseBuilder()

    def test_builder_creates_request_id(self):
        """Each builder instance should have a unique request_id."""
        builder2 = ErrorResponseBuilder()
        self.assertIsNotNone(self.builder._request_id)
        self.assertNotEqual(self.builder._request_id, builder2._request_id)

    def test_format_error_basic_structure(self):
        """Error response must have required top-level keys."""
        response = self.builder.format_error(TIMEOUT)

        self.assertFalse(response["success"])
        self.assertIn("error", response)
        self.assertIn("timestamp", response)
        self.assertIn("request_id", response)
        self.assertIn("context", response)

    def test_format_error_error_object_structure(self):
        """Error object must contain all required fields."""
        response = self.builder.format_error(TIMEOUT)
        error = response["error"]

        self.assertEqual(error["code"], "TIMEOUT")
        self.assertEqual(error["message"], TIMEOUT.message)
        self.assertEqual(error["category"], TIMEOUT.category.value)
        self.assertEqual(error["retryable"], TIMEOUT.retryable)
        self.assertEqual(error["http_status_analogy"], TIMEOUT.http_status_analogy)
        self.assertIsInstance(error["suggestions"], list)
        self.assertIsInstance(error["recovery_actions"], list)

    def test_format_error_with_action_and_session(self):
        """Context fields should be populated when provided."""
        response = self.builder.format_error(
            TIMEOUT,
            action="tab list",
            session_id="abc123",
        )
        context = response["context"]

        self.assertEqual(context["action"], "tab list")
        self.assertEqual(context["session_id"], "abc123")

    def test_format_error_with_custom_details(self):
        """Custom details should appear in context.details."""
        custom_details = {"element": "#login-btn", "timeout": 30}
        response = self.builder.format_error(
            TIMEOUT,
            details=custom_details,
        )

        self.assertEqual(response["context"]["details"], custom_details)

    def test_format_error_auto_populates_suggestions(self):
        """Suggestions should auto-populate from template if not provided."""
        response = self.builder.format_error(TIMEOUT)
        suggestions = response["error"]["suggestions"]

        self.assertGreater(len(suggestions), 0)
        self.assertIn(suggestions, [SUGGESTION_MAP["TIMEOUT"]])

    def test_format_error_custom_suggestions_override_template(self):
        """Custom suggestions should replace template suggestions."""
        custom = ["Custom suggestion 1", "Custom suggestion 2"]
        response = self.builder.format_error(
            TIMEOUT,
            suggestions=custom,
        )

        self.assertEqual(response["error"]["suggestions"], custom)

    def test_format_error_auto_populates_recovery_actions(self):
        """Recovery actions should auto-populate if template exists."""
        response = self.builder.format_error(DAEMON_CRASHED)
        recovery = response["error"]["recovery_actions"]

        # DAEMON_CRASHED has recovery templates
        self.assertGreater(len(recovery), 0)

    def test_format_error_no_recovery_for_unknown_error(self):
        """Errors without recovery templates should have empty list."""
        response = self.builder.format_error(INVALID_PARAMS)
        recovery = response["error"]["recovery_actions"]

        # INVALID_PARAMS has no recovery template
        self.assertEqual(recovery, [])

    def test_format_success_basic_structure(self):
        """Success response must have required fields."""
        response = self.builder.format_success({"tabs": []})

        self.assertTrue(response["success"])
        self.assertIn("data", response)
        self.assertIn("timestamp", response)
        self.assertIn("request_id", response)
        self.assertIn("context", response)

    def test_format_success_wraps_data(self):
        """Data should be preserved as-is."""
        test_data = {"id": 1, "name": "test"}
        response = self.builder.format_success(test_data)

        self.assertEqual(response["data"], test_data)

    def test_format_success_with_metadata(self):
        """Metadata should be stored in context."""
        response = self.builder.format_success(
            data=[],
            action="tab list",
            session_id="sess1",
            metadata={"duration_ms": 150},
        )

        self.assertEqual(response["context"]["action"], "tab list")
        self.assertEqual(response["context"]["session_id"], "sess1")
        self.assertEqual(response["context"]["metadata"]["duration_ms"], 150)

    def test_to_json_pretty_print(self):
        """Pretty JSON should be indented."""
        response = self.builder.format_error(TIMEOUT)
        json_str = self.builder.to_json(response, pretty=True)

        parsed = json.loads(json_str)
        self.assertEqual(parsed["error"]["code"], "TIMEOUT")
        self.assertIn("\n", json_str)  # Has newlines from indentation

    def test_to_json_compact(self):
        """Compact JSON should be single line."""
        response = self.builder.format_error(TIMEOUT)
        json_str = self.builder.to_json(response, pretty=False)

        parsed = json.loads(json_str)
        self.assertEqual(parsed["error"]["code"], "TIMEOUT")
        self.assertNotIn("\n", json_str.strip())

    def test_timestamp_is_iso_format(self):
        """Timestamp should be valid ISO 8601 format."""
        response = self.builder.format_error(TIMEOUT)
        timestamp = response["timestamp"]

        # Should parse without error
        parsed = datetime.fromisoformat(timestamp)
        self.assertIsInstance(parsed, datetime)

    def test_request_id_is_unique_per_builder(self):
        """Different builders should have different request IDs."""
        builder_a = ErrorResponseBuilder()
        builder_b = ErrorResponseBuilder()

        resp_a = builder_a.format_error(TIMEOUT)
        resp_b = builder_b.format_error(TIMEOUT)

        self.assertNotEqual(resp_a["request_id"], resp_b["request_id"])

    def test_context_details_default_empty_dict(self):
        """Details should default to empty dict if not provided."""
        response = self.builder.format_error(TIMEOUT)

        self.assertEqual(response["context"]["details"], {})


class TestConvenienceFunctions(unittest.TestCase):
    """Test module-level convenience functions."""

    def test_build_error_response(self):
        """build_error_response should create valid error response."""
        response = build_error_response(
            TIMEOUT,
            action="click",
            session_id="s1",
        )

        self.assertFalse(response["success"])
        self.assertEqual(response["error"]["code"], "TIMEOUT")
        self.assertEqual(response["context"]["action"], "click")

    def test_build_success_response(self):
        """build_success_response should create valid success response."""
        response = build_success_response(
            {"result": "ok"},
            action="navigate",
        )

        self.assertTrue(response["success"])
        self.assertEqual(response["data"], {"result": "ok"})
        self.assertEqual(response["context"]["action"], "navigate")


class TestSuggestionAndRecoveryTemplates(unittest.TestCase):
    """Test suggestion and recovery action templates."""

    def test_suggestion_templates_exist_for_key_errors(self):
        """Common errors should have suggestion templates."""
        errors_with_suggestions = ["TIMEOUT", "CONNECTION_LOST", "INVALID_PARAMS",
                                   "AUTH_FAILED", "DAEMON_CRASHED"]

        for error_code in errors_with_suggestions:
            with self.subTest(error=error_code):
                self.assertIn(error_code, SUGGESTION_MAP)
                self.assertGreater(len(SUGGESTION_MAP[error_code]), 0)

    def test_recovery_templates_exist_for_some_errors(self):
        """Some critical errors should have recovery action templates."""
        errors_with_recovery = ["TIMEOUT", "CONNECTION_LOST", "DAEMON_CRASHED"]

        for error_code in errors_with_recovery:
            with self.subTest(error=error_code):
                self.assertIn(error_code, RECOVERY_MAP)

    def test_recovery_actions_have_required_fields(self):
        """Recovery actions should have action, command, description."""
        for error_code, actions in RECOVERY_MAP.items():
            for action in actions:
                with self.subTest(error=error_code, action=action["action"]):
                    self.assertIn("action", action)
                    self.assertIn("command", action)
                    self.assertIn("description", action)


class TestJsonSerialization(unittest.TestCase):
    """Test that all responses are JSON-serializable."""

    def test_error_response_serializable(self):
        builder = ErrorResponseBuilder()
        response = builder.format_error(DAEMON_CRASHED, details={"key": "value"})

        # Should not raise
        json_str = json.dumps(response, ensure_ascii=False)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["success"], False)

    def test_success_response_serializable(self):
        builder = ErrorResponseBuilder()
        response = builder.format_success(
            data={"items": [1, 2, 3]},
            metadata={"count": 3},
        )

        json_str = json.dumps(response, ensure_ascii=False)
        parsed = json.loads(json_str)
        self.assertTrue(parsed["success"])
        self.assertEqual(len(parsed["data"]["items"]), 3)

    def test_unicode_handling(self):
        """JSON should handle unicode characters correctly."""
        builder = ErrorResponseBuilder()
        response = builder.format_error(
            INVALID_PARAMS,
            details={"message": "测试中文"},
        )

        json_str = builder.to_json(response)
        self.assertIn("测试中文", json_str)


if __name__ == "__main__":
    unittest.main()
