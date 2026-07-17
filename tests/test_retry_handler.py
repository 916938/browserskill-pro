"""
Unit tests for retry_handler module
"""

import sys
import os
import time
import unittest
from unittest.mock import patch, MagicMock

# Add skill/scripts to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skill', 'scripts'))

from retry_handler import (
    RetryConfig,
    RetryHandler,
    AttemptResult,
    RetrySummary,
    retry_on_transient_error,
    DEFAULT_HANDLER,
    AGGRESSIVE_HANDLER,
    CONSERVATIVE_HANDLER,
)
from error_codes import TIMEOUT, CONNECTION_LOST, INVALID_PARAMS, classify_exception


class TestRetryConfig(unittest.TestCase):
    """Test RetryConfig dataclass."""

    def test_default_values(self):
        config = RetryConfig()
        self.assertEqual(config.max_retries, 3)
        self.assertEqual(config.base_delay, 1.0)
        self.assertEqual(config.max_delay, 30.0)
        self.assertAlmostEqual(config.jitter_percentage, 0.2)

    def test_custom_config(self):
        config = RetryConfig(max_retries=5, base_delay=2.0)
        self.assertEqual(config.max_retries, 5)
        self.assertEqual(config.base_delay, 2.0)

    def test_default_retryable_errors(self):
        config = RetryConfig()
        self.assertIn(TIMEOUT, config.retryable_errors)
        self.assertIn(CONNECTION_LOST, config.retryable_errors)
        self.assertNotIn(INVALID_PARAMS, config.retryable_errors)


class TestRetryHandlerDelayCalculation(unittest.TestCase):
    """Test exponential backoff with jitter."""

    def setUp(self):
        self.handler = RetryHandler(RetryConfig(
            base_delay=1.0,
            backoff_multiplier=2.0,
            max_delay=30.0,
            jitter_percentage=0.0,  # No jitter for deterministic tests
        ))

    def test_first_attempt_delay_zero(self):
        """First attempt should have no delay."""
        delay = self.handler.calculate_delay(0)  # attempt 0 = before first retry
        self.assertEqual(delay, 0.0)

    def test_exponential_growth(self):
        """Delays should grow exponentially."""
        # Skip attempt 0 (returns 0), start from attempt 1
        delay_1 = self.handler.calculate_delay(1)   # Before attempt 2 (first retry)
        delay_2 = self.handler.calculate_delay(2)   # Before attempt 3 (second retry)
        delay_3 = self.handler.calculate_delay(3)   # Before attempt 4 (third retry)

        self.assertGreater(delay_2, delay_1)
        self.assertGreater(delay_3, delay_2)
        # Should roughly double each time (with no jitter)
        self.assertAlmostEqual(delay_2 / delay_1 if delay_1 > 0 else 0, 2.0, places=0)
        self.assertAlmostEqual(delay_3 / delay_2 if delay_2 > 0 else 0, 2.0, places=0)

    def test_max_delay_cap(self):
        """Delays should not exceed max_delay."""
        handler_with_cap = RetryHandler(RetryConfig(
            base_delay=10.0,
            backoff_multiplier=10.0,
            max_delay=20.0,
            jitter_percentage=0.0,
        ))

        delay = handler_with_cap.calculate_delay(5)  # Would be huge without cap
        self.assertLessEqual(delay, 20.0)

    def test_jitter_adds_variance(self):
        """Jitter should produce different delays on multiple calls."""
        handler_with_jitter = RetryHandler(RetryConfig(
            base_delay=1.0,
            jitter_percentage=0.2,
        ))

        delays = [handler_with_jitter.calculate_delay(1) for _ in range(10)]
        # Should have some variance (not all identical)
        unique_delays = set(delays)
        self.assertGreater(len(unique_delays), 1, "Jitter should produce varied delays")

    def test_jitter_within_bounds(self):
        """With ±20% jitter, delay should be within [0.8x, 1.2x] of base."""
        handler = RetryHandler(RetryConfig(
            base_delay=10.0,
            jitter_percentage=0.2,
        ))

        for _ in range(50):  # Statistical check
            delay = handler.calculate_delay(1)  # Use attempt >= 1
            self.assertGreaterEqual(delay, 8.0)   # 80% of base
            self.assertLessEqual(delay, 12.0)      # 120% of base


class TestShouldRetryLogic(unittest.TestCase):
    """Test retry decision logic."""

    def setUp(self):
        self.handler = DEFAULT_HANDLER

    def test_should_retry_timeout(self):
        self.assertTrue(self.handler.should_retry(error=TIMEOUT))

    def test_should_retry_connection_lost(self):
        self.assertTrue(self.handler.should_retry(error=CONNECTION_LOST))

    def test_should_not_retry_invalid_params(self):
        self.assertFalse(self.handler.should_retry(error=INVALID_PARAMS))

    def test_max_retries_limit(self):
        """Should stop after max_retries attempts."""
        for i in range(DEFAULT_HANDLER.config.max_retries + 1):
            result = self.handler.should_retry(error=TIMEOUT, current_attempt=i)
            if i >= DEFAULT_HANDLER.config.max_retries:
                self.assertFalse(result, f"Should not retry after {DEFAULT_HANDLER.config.max_retries} attempts")
            else:
                self.assertTrue(result, f"Should retry on attempt {i}")

    def test_should_retry_connection_error_exception(self):
        self.assertTrue(self.handler.should_retry(exception=ConnectionError("refused")))

    def test_should_not_retry_value_error(self):
        self.assertFalse(self.handler.should_retry(exception=ValueError("bad value")))

    def test_retry_on_exit_code_timeout(self):
        """Exit code 2 maps to TIMEOUT which is retryable."""
        self.assertTrue(self.handler.should_retry(exit_code=2))

    def test_no_retry_on_exit_code_invalid_params(self):
        """Exit code 1 maps to INVALID_PARAMS which is not retryable."""
        self.assertFalse(self.handler.should_retry(exit_code=1))


class TestExecuteWithRetry(unittest.TestCase):
    """Test the main retry execution logic."""

    def setUp(self):
        self.handler = RetryHandler(RetryConfig(
            max_retries=3,
            base_delay=0.01,  # Very short for fast tests
            jitter_percentage=0.0,
            overall_timeout=10.0,
        ))

    def test_success_first_attempt(self):
        """Function succeeding immediately should return without retries."""
        mock_func = MagicMock(return_value="success")

        result, summary = self.handler.execute_with_retry(mock_func)

        self.assertEqual(result, "success")
        self.assertTrue(summary.succeeded)
        self.assertEqual(summary.total_attempts, 1)
        self.assertFalse(summary.was_retried)
        mock_func.assert_called_once()

    def test_success_after_retries(self):
        """Function failing then succeeding should show correct stats."""
        call_count = [0]

        def flaky_func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ConnectionError("temporary failure")
            return "eventual success"

        result, summary = self.handler.execute_with_retry(flaky_func)

        self.assertEqual(result, "eventual success")
        self.assertTrue(summary.succeeded)
        self.assertEqual(summary.total_attempts, 3)
        self.assertTrue(summary.was_retried)
        self.assertEqual(call_count[0], 3)

    def test_all_retries_exhausted(self):
        """All retries exhausted should raise last exception."""
        def always_fail():
            raise TimeoutError("persistent timeout")

        with self.assertRaises(TimeoutError):
            self.handler.execute_with_retry(always_fail)

    def test_non_retryable_error_fails_immediately(self):
        """Non-retryable errors should fail on first attempt."""
        def bad_params():
            raise ValueError("invalid input")

        with self.assertRaises(ValueError):
            self.handler.execute_with_retry(bad_params)

    def test_summary_contains_all_attempts(self):
        """Summary should record all attempt details."""
        call_count = [0]

        def intermittent():
            call_count[0] += 1
            if call_count[0] % 2 == 1:  # Fail on odd attempts
                raise ConnectionError("intermittent")
            return "ok"

        result, summary = self.handler.execute_with_retry(intermittent)

        # Should have at least 2 attempts (fail, succeed)
        self.assertGreaterEqual(len(summary.attempts), 2)
        for attempt in summary.attempts:
            self.assertIsInstance(attempt, AttemptResult)
            self.assertIn("attempt_number", dir(attempt))

    def test_overall_timeout_respected(self):
        """Should stop if overall timeout exceeded."""
        slow_handler = RetryHandler(RetryConfig(
            max_retries=100,
            base_delay=0.01,
            overall_timeout=0.05,  # Very short timeout
            jitter_percentage=0.0,
        ))

        def slow_failure():
            time.sleep(0.02)  # Each attempt takes 20ms
            raise TimeoutError("slow")

        start = time.time()
        with self.assertRaises(TimeoutError):
            slow_handler.execute_with_retry(slow_failure)
        elapsed = time.time() - start

        # Should complete well under 1 second due to timeout
        self.assertLess(elapsed, 1.0)

    def test_arguments_passed_through(self):
        """Arguments and kwargs should be passed to function correctly."""
        mock_func = MagicMock(return_value="result")

        self.handler.execute_with_retry(mock_func, "arg1", "arg2", key="value")

        mock_func.assert_called_once_with("arg1", "arg2", key="value")


class TestDecoratorUsage(unittest.TestCase):
    """Test decorator-based retry usage."""

    def test_basic_decorator(self):
        """Decorator should wrap function correctly."""
        handler = RetryHandler(RetryConfig(
            max_retries=2,
            base_delay=0.01,
            jitter_percentage=0.0,
        ))

        @handler.retry
        def decorated_func(x):
            return x * 2

        result, summary = decorated_func(5)
        self.assertEqual(result, 10)
        self.assertTrue(summary.succeeded)

    def test_decorator_preserves_function_name(self):
        """@functools.wraps should preserve metadata."""
        handler = DEFAULT_HANDLER

        @handler.retry
        def my_function():
            pass

        self.assertEqual(my_function.__name__, "my_function")


class TestConvenienceDecorator(unittest.TestCase):
    """Test retry_on_transient_error convenience decorator."""

    def test_convenience_decorator_basic(self):
        @retry_on_transient_error(max_retries=2, base_delay=0.01, jitter_percentage=0.0)
        def quick_operation():
            return "done"

        result, summary = quick_operation()
        self.assertEqual(result, "done")
        self.assertTrue(summary.succeeded)


class TestPreconfiguredHandlers(unittest.TestCase):
    """Test pre-built handler configurations."""

    def test_default_handler_exists(self):
        self.assertIsInstance(DEFAULT_HANDLER, RetryHandler)

    def test_aggressive_handler_more_retries(self):
        self.assertGreater(AGGRESSIVE_HANDLER.config.max_retries, DEFAULT_HANDLER.config.max_retries)

    def test_conservative_handler_fewer_retries(self):
        self.assertLess(CONSERVATIVE_HANDLER.config.max_retries, DEFAULT_HANDLER.config.max_retries)

    def test_aggressive_handler_shorter_base_delay(self):
        self.assertLess(AGGRESSIVE_HANDLER.config.base_delay, DEFAULT_HANDLER.config.base_delay)

    def test_conservative_handler_longer_base_delay(self):
        self.assertGreater(CONSERVATIVE_HANDLER.config.base_delay, DEFAULT_HANDLER.config.base_delay)


class TestRetrySummarySerialization(unittest.TestCase):
    """Test RetrySummary.to_dict() method."""

    def test_successful_summary_dict(self):
        handler = RetryHandler(RetryConfig(jitter_percentage=0.0))
        mock_func = MagicMock(return_value="data")

        _, summary = handler.execute_with_retry(mock_func)
        d = summary.to_dict()

        self.assertTrue(d["succeeded"])
        self.assertEqual(d["total_attempts"], 1)
        self.assertIn("final_error", d)
        self.assertIsNone(d["final_error"])

    def test_failed_summary_dict(self):
        handler = RetryHandler(RetryConfig(
            max_retries=1,
            base_delay=0.01,
            jitter_percentage=0.0,
        ))

        def fail_once_then_succeed():
            if not hasattr(fail_once_then_succeed, "called"):
                fail_once_then_succeed.called = True
                raise ConnectionError("temp")
            return "recovered"

        _, summary = handler.execute_with_retry(fail_once_then_succeed)
        d = summary.to_dict()

        self.assertTrue(d["succeeded"])
        self.assertTrue(d["was_retried"])


class TestEdgeCases(unittest.TestCase):
    """Edge case tests."""

    def test_zero_retries_config(self):
        """max_retries=0 means no retries at all."""
        handler = RetryHandler(RetryConfig(max_retries=0))

        def always_fail():
            raise TimeoutError("fail")

        with self.assertRaises(TimeoutError):
            handler.execute_with_retry(always_fail)

    def test_function_returning_none(self):
        """Functions returning None should be handled correctly."""
        handler = DEFAULT_HANDLER

        mock_func = MagicMock(return_value=None)
        result, summary = handler.execute_with_retry(mock_func)

        self.assertIsNone(result)
        self.assertTrue(summary.succeeded)

    def test_large_base_delay_with_jitter(self):
        """Large delays should still work correctly."""
        handler = RetryHandler(RetryConfig(base_delay=100.0, jitter_percentage=0.3, max_delay=200.0))
        delay = handler.calculate_delay(1)  # Use attempt >= 1
        # Should be around 100s with ±30s jitter
        self.assertGreater(delay, 50.0)
        self.assertLess(delay, 200.0)


if __name__ == "__main__":
    unittest.main()
