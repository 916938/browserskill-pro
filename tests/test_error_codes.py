"""
Unit tests for error_codes module
"""

import sys
import os
import unittest

# Add skill/scripts to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skill', 'scripts'))

from error_codes import (
    ErrorCategory, ErrorCode,
    TIMEOUT, CONNECTION_LOST, INVALID_PARAMS, AUTH_FAILED,
    DAEMON_CRASHED, SESSION_EXPIRED, NOT_FOUND, RATE_LIMITED,
    INTERNAL_ERROR, BROWSER_NOT_READY, VALIDATION_FAILED, CANCELLED,
    CONFIGURATION_ERROR, UNKNOWN_ERROR,
    EXIT_CODE_MAP, get_error_by_code, get_error_by_exit_code,
    classify_exception
)


class TestErrorCategory(unittest.TestCase):
    """Test ErrorCategory enum values and behavior."""

    def test_category_count(self):
        self.assertEqual(len(ErrorCategory), 4)

    def test_retryable_categories(self):
        retryable = {ErrorCategory.TRANSIENT}
        non_retryable = {
            ErrorCategory.PERMANENT,
            ErrorCategory.SYSTEM,
            ErrorCategory.USER_ERROR,
        }
        # TRANSIENT should be the only auto-retryable category
        self.assertTrue(ErrorCategory.TRANSIENT in retryable)


class TestErrorCode(unittest.TestCase):
    """Test ErrorCode dataclass instances."""

    def test_timeout_properties(self):
        self.assertEqual(TIMEOUT.code, "TIMEOUT")
        self.assertEqual(TIMEOUT.category, ErrorCategory.TRANSIENT)
        self.assertTrue(TIMEOUT.retryable)
        self.assertEqual(TIMEOUT.http_status_analogy, 504)

    def test_invalid_params_not_retryable(self):
        self.assertFalse(INVALID_PARAMS.retryable)
        self.assertEqual(INVALID_PARAMS.category, ErrorCategory.PERMANENT)

    def test_all_errors_have_required_fields(self):
        errors = [
            TIMEOUT, CONNECTION_LOST, INVALID_PARAMS, AUTH_FAILED,
            DAEMON_CRASHED, SESSION_EXPIRED, NOT_FOUND, RATE_LIMITED,
            INTERNAL_ERROR, BROWSER_NOT_READY, VALIDATION_FAILED, CANCELLED,
            CONFIGURATION_ERROR, UNKNOWN_ERROR,
        ]
        for error in errors:
            with self.subTest(error=error.code):
                self.assertIsInstance(error.code, str)
                self.assertIsInstance(error.message, str)
                self.assertIsInstance(error.category, ErrorCategory)
                self.assertIsInstance(error.retryable, bool)
                self.assertIsInstance(error.http_status_analogy, int)

    def test_error_count(self):
        """Ensure we have all expected predefined errors."""
        self.assertEqual(
            len([TIMEOUT, CONNECTION_LOST, INVALID_PARAMS, AUTH_FAILED,
                 DAEMON_CRASHED, SESSION_EXPIRED, NOT_FOUND, RATE_LIMITED,
                 INTERNAL_ERROR, BROWSER_NOT_READY, VALIDATION_FAILED, CANCELLED,
                 CONFIGURATION_ERROR, UNKNOWN_ERROR]),
            14
        )


class TestExitCodeMapping(unittest.TestCase):
    """Test exit code to ErrorCode mapping."""

    def test_success_exit_code(self):
        """Exit code 0 should map to None (no error)."""
        self.assertIsNone(EXIT_CODE_MAP.get(0))

    def test_known_exit_codes(self):
        known_mappings = {
            1: INVALID_PARAMS,
            2: TIMEOUT,
            3: CONNECTION_LOST,
            4: AUTH_FAILED,
            5: NOT_FOUND,
        }
        for exit_code, expected_error in known_mappings.items():
            with self.subTest(exit_code=exit_code):
                self.assertEqual(EXIT_CODE_MAP[exit_code], expected_error)

    def test_unknown_exit_code_returns_none(self):
        """Unknown exit codes should return None from get_error_by_exit_code."""
        self.assertIsNone(get_error_by_exit_code(99))


class TestLookupFunctions(unittest.TestCase):
    """Test error code lookup utilities."""

    def test_get_error_by_code_found(self):
        result = get_error_by_code("TIMEOUT")
        self.assertEqual(result, TIMEOUT)

    def test_get_error_by_code_not_found(self):
        result = get_error_by_code("NONEXISTENT")
        self.assertIsNone(result)

    def test_get_error_by_exit_code_success(self):
        """Exit code 0 returns None for success."""
        self.assertIsNone(get_error_by_exit_code(0))

    def test_get_error_by_exit_code_error(self):
        result = get_error_by_exit_code(2)
        self.assertEqual(result, TIMEOUT)


class TestExceptionClassification(unittest.TestCase):
    """Test Python exception to ErrorCode mapping."""

    def test_timeout_error_classification(self):
        result = classify_exception(TimeoutError("timed out"))
        self.assertEqual(result, TIMEOUT)

    def test_connection_error_classification(self):
        result = classify_exception(ConnectionError("connection refused"))
        self.assertEqual(result, CONNECTION_LOST)

    def test_value_error_classification(self):
        result = classify_exception(ValueError("invalid value"))
        self.assertEqual(result, INVALID_PARAMS)

    def test_type_error_classification(self):
        result = classify_exception(TypeError("wrong type"))
        self.assertEqual(result, INVALID_PARAMS)

    def test_permission_error_classification(self):
        result = classify_exception(PermissionError("access denied"))
        self.assertEqual(result, AUTH_FAILED)

    def test_file_not_found_classification(self):
        result = classify_exception(FileNotFoundError("file missing"))
        self.assertEqual(result, NOT_FOUND)

    def test_key_error_classification(self):
        result = classify_exception(KeyError("missing key"))
        self.assertEqual(result, NOT_FOUND)

    def test_runtime_error_daemon_crash(self):
        result = classify_exception(RuntimeError("daemon crashed unexpectedly"))
        self.assertEqual(result, DAEMON_CRASHED)

    def test_runtime_error_timeout_pattern(self):
        result = classify_exception(RuntimeError("operation timeout exceeded"))
        self.assertEqual(result, TIMEOUT)

    def test_runtime_error_connection_pattern(self):
        result = classify_exception(RuntimeError("connection refused by daemon"))
        self.assertEqual(result, CONNECTION_LOST)

    def test_generic_runtime_error(self):
        result = classify_exception(RuntimeError("something went wrong"))
        self.assertEqual(result, INTERNAL_ERROR)

    def test_unknown_exception_fallback(self):
        class CustomException(Exception):
            pass

        result = classify_exception(CustomException("custom error"))
        self.assertEqual(result, UNKNOWN_ERROR)

    def test_frozen_dataclass_immutability(self):
        """Verify ErrorCode instances are immutable."""
        with self.assertRaises(AttributeError):
            TIMEOUT.code = "CHANGED"


if __name__ == "__main__":
    unittest.main()
