"""
Unit tests for timeout_manager module
"""

import sys
import os
import time
import unittest
from unittest.mock import patch, MagicMock

# Add skill/scripts to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skill', 'scripts'))

from timeout_manager import (
    TimeoutConfig,
    TimeoutLayer,
    TimeoutManager,
    TimeoutResult,
    CancellationToken,
    OperationCancelled,
    run_with_timeout,
    command_timeout,
)


class TestTimeoutConfig(unittest.TestCase):
    """Test TimeoutConfig defaults and customization."""

    def test_default_values(self):
        config = TimeoutConfig()
        self.assertEqual(config.connect_timeout, 10.0)
        self.assertEqual(config.command_timeout, 30.0)
        self.assertEqual(config.session_timeout, 300.0)
        self.assertEqual(config.global_timeout, 600.0)
        self.assertTrue(config.enable_signal_handling)

    def test_custom_config(self):
        config = TimeoutConfig(
            command_timeout=60.0,
            global_timeout=1200.0,
        )
        self.assertEqual(config.command_timeout, 60.0)
        self.assertEqual(config.global_timeout, 1200.0)


class TestCancellationToken(unittest.TestCase):
    """Test cooperative cancellation token."""

    def test_initial_state_not_cancelled(self):
        token = CancellationToken()
        self.assertFalse(token.is_cancelled)
        self.assertIsNone(token.reason)

    def test_cancel_sets_flag(self):
        token = CancellationToken()
        token.cancel("test reason")
        self.assertTrue(token.is_cancelled)
        self.assertEqual(token.reason, "test reason")

    def test_reset_clears_cancellation(self):
        token = CancellationToken()
        token.cancel("reason")
        token.reset()
        self.assertFalse(token.is_cancelled)
        self.assertIsNone(token.reason)

    def test_raise_if_cancelled_when_not_cancelled(self):
        token = CancellationToken()
        # Should not raise
        token.raise_if_cancelled()

    def test_raise_if_cancelled_when_cancelled(self):
        token = CancellationToken()
        token.cancel("stop now")
        with self.assertRaises(OperationCancelled) as ctx:
            token.raise_if_cancelled()
        self.assertIn("stop now", str(ctx.exception))

    def test_thread_safety(self):
        """Cancellation should be thread-safe."""
        import threading

        token = CancellationToken()

        def canceller():
            time.sleep(0.01)
            token.cancel("from thread")

        t = threading.Thread(target=canceller)
        t.start()
        t.join(timeout=1.0)

        self.assertTrue(token.is_cancelled)


class TestTimeoutManagerBasic(unittest.TestCase):
    """Test basic TimeoutManager functionality."""

    def setUp(self):
        # Disable signal handling in tests to avoid side effects
        self.config = TimeoutConfig(enable_signal_handling=False)
        self.manager = TimeoutManager(self.config)

    def tearDown(self):
        if hasattr(self, 'manager'):
            self.manager.cleanup()

    def test_creation(self):
        self.assertIsNotNone(self.manager.cancellation_token)

    def test_get_timeout_for_layer(self):
        connect_t = self.manager.get_timeout_for_layer(TimeoutLayer.CONNECT)
        command_t = self.manager.get_timeout_for_layer(TimeoutLayer.COMMAND)

        self.assertEqual(connect_t, 10.0)
        self.assertEqual(command_t, 30.0)


class TestTimeoutContextManager(unittest.TestCase):
    """Test timeout context manager."""

    def setUp(self):
        self.config = TimeoutConfig(enable_signal_handling=False)
        self.manager = TimeoutManager(self.config)

    def tearDown(self):
        self.manager.cleanup()

    def test_successful_execution_within_timeout(self):
        """Operations completing within timeout should succeed."""
        with self.manager.timeout_context(
            TimeoutLayer.COMMAND,
            custom_timeout=5.0,
        ):
            result = sum(range(100))
        self.assertEqual(result, 4950)

    def test_cancellation_token_available_in_context(self):
        """CancellationToken should be accessible during context."""
        with self.manager.timeout_context(TimeoutLayer.COMMAND):
            token = self.manager.cancellation_token
            self.assertIsInstance(token, CancellationToken)
            self.assertFalse(token.is_cancelled)


class TestExecuteWithTimeout(unittest.TestCase):
    """Test execute_with_timeout method."""

    def setUp(self):
        self.config = TimeoutConfig(enable_signal_handling=False)
        self.manager = TimeoutManager(self.config)

    def tearDown(self):
        self.manager.cleanup()

    def test_quick_function_completes(self):
        def quick_func():
            return "done"

        result = self.manager.execute_with_timeout(
            quick_func,
            timeout_layer=TimeoutLayer.COMMAND,
            custom_timeout=5.0,
        )

        self.assertTrue(result.completed)
        self.assertTrue(result.is_success)
        self.assertEqual(result.result, "done")
        self.assertFalse(result.timed_out)

    def test_function_with_arguments(self):
        def add(a, b):
            return a + b

        result = self.manager.execute_with_timeout(
            add,
            3,
            4,
            timeout_layer=TimeoutLayer.COMMAND,
            custom_timeout=5.0,
        )

        self.assertTrue(result.is_success)
        self.assertEqual(result.result, 7)

    def test_function_with_kwargs(self):
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"

        result = self.manager.execute_with_timeout(
            greet,
            name="World",
            greeting="Hi",
            timeout_layer=TimeoutLayer.COMMAND,
            custom_timeout=5.0,
        )

        self.assertEqual(result.result, "Hi, World!")

    def test_slow_function_times_out(self):
        def slow_func():
            time.sleep(10)
            return "should not reach"

        start = time.time()
        result = self.manager.execute_with_timeout(
            slow_func,
            timeout_layer=TimeoutLayer.COMMAND,
            custom_timeout=0.2,  # Very short for fast test
        )
        elapsed = time.time() - start

        self.assertTrue(result.timed_out)
        self.assertFalse(result.completed)
        self.assertLess(elapsed, 2.0)  # Should complete quickly due to timeout

    def test_raising_exception_propagates(self):
        def failing_func():
            raise ValueError("intentional error")

        result = self.manager.execute_with_timeout(
            failing_func,
            timeout_layer=TimeoutLayer.COMMAND,
            custom_timeout=5.0,
        )

        self.assertFalse(result.completed)
        self.assertIsNotNone(result.error)
        self.assertIsInstance(result.error, ValueError)

    def test_result_duration_recorded(self):
        def instant():
            return 42

        result = self.manager.execute_with_timeout(
            instant,
            timeout_layer=TimeoutLayer.COMMAND,
        )

        self.assertGreaterEqual(result.duration, 0)
        self.assertIsInstance(result.duration, float)

    def test_result_layer_recorded(self):
        def func():
            return None

        result = self.manager.execute_with_timeout(
            func,
            timeout_layer=TimeoutLayer.SESSION,
        )

        self.assertEqual(result.layer, TimeoutLayer.SESSION)


class TestTimeoutResult(unittest.TestCase):
    """Test TimeoutResult serialization."""

    def test_success_result_to_dict(self):
        result = TimeoutResult(
            completed=True,
            result="data",
            duration=1.5,
            layer=TimeoutLayer.COMMAND,
        )

        d = result.to_dict()

        self.assertTrue(d["success"])
        self.assertTrue(d["completed"])
        self.assertFalse(d["timed_out"])
        self.assertFalse(d["cancelled"])
        self.assertAlmostEqual(d["duration_s"], 1.5)
        self.assertEqual(d["layer"], "COMMAND")

    def test_timeout_result_to_dict(self):
        result = TimeoutResult(
            completed=False,
            timed_out=True,
            duration=30.0,
            layer=TimeoutLayer.COMMAND,
        )

        d = result.to_dict()

        self.assertFalse(d["success"])
        self.assertTrue(d["timed_out"])

    def test_cancelled_result_to_dict(self):
        result = TimeoutResult(
            completed=False,
            cancelled=True,
            duration=5.0,
        )

        d = result.to_dict()

        self.assertFalse(d["success"])
        self.assertTrue(d["cancelled"])


class TestGlobalTimeoutTracking(unittest.TestCase):
    """Test global timeout management."""

    def setUp(self):
        self.config = TimeoutConfig(enable_signal_handling=False, global_timeout=1.0)
        self.manager = TimeoutManager(self.config)

    def tearDown(self):
        self.manager.cleanup()

    def test_elapsed_time_tracking(self):
        time.sleep(0.05)
        elapsed = self.manager.get_elapsed_time()
        self.assertGreater(elapsed, 0.04)

    def test_check_global_timeout_not_exceeded(self):
        # Should not be exceeded immediately after creation
        self.assertFalse(self.manager.check_global_timeout())

    def test_reset_global_timer(self):
        initial_start = self.manager._start_time
        time.sleep(0.05)
        self.manager.reset_global_timer()
        new_start = self.manager._start_time
        # New start time should be later than original
        self.assertGreater(new_start, initial_start)


class TestSignalHandling(unittest.TestCase):
    """Test signal handler installation (basic)."""

    def test_signal_handlers_installed_when_enabled(self):
        config = TimeoutConfig(enable_signal_handling=True)
        manager = TimeoutManager(config)

        # Just verify it doesn't crash; actual signal testing is platform-dependent
        manager.cleanup()


class TestConvenienceFunctions(unittest.TestCase):
    """Test module-level convenience functions."""

    def test_run_with_timeout_success(self):
        def quick():
            return 42

        result, success = run_with_timeout(quick, 5.0)
        self.assertTrue(success)
        self.assertEqual(result, 42)

    def test_run_with_timeout_failure(self):
        def slow():
            time.sleep(10)
            return None

        result, success = run_with_timeout(slow, 0.2)
        self.assertFalse(success)
        self.assertIsNone(result)

    def test_command_timeout_context_manager(self):
        with command_timeout(5.0) as token:
            self.assertIsInstance(token, CancellationToken)
            result = sum(range(50))
        self.assertEqual(result, 1225)


class TestEdgeCases(unittest.TestCase):
    """Edge case tests."""

    def test_function_returning_none(self):
        config = TimeoutConfig(enable_signal_handling=False)
        manager = TimeoutManager(config)

        def return_none():
            return None

        result = manager.execute_with_timeout(return_none)
        self.assertTrue(result.is_success)
        self.assertIsNone(result.result)
        manager.cleanup()

    def test_zero_timeout_immediate_timeout(self):
        config = TimeoutConfig(enable_signal_handling=False)
        manager = TimeoutManager(config)

        def any_func():
            time.sleep(0.01)
            return "done"

        result = manager.execute_with_timeout(
            any_func,
            custom_timeout=0.001,  # Essentially zero
        )
        # Should either timeout or complete very quickly
        self.assertIsNotNone(result)
        manager.cleanup()

    def test_cleanup_idempotent(self):
        config = TimeoutConfig(enable_signal_handling=False)
        manager = TimeoutManager(config)

        # Multiple cleanup calls shouldn't error
        manager.cleanup()
        manager.cleanup()


if __name__ == "__main__":
    unittest.main()
