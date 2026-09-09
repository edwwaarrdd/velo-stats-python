import unittest

from tasks.tasks import log_test_message


class LogTestMessageTests(unittest.TestCase):
    def test_runs_synchronously_and_logs_message(self):
        with self.assertLogs("tasks", level="INFO") as captured:
            log_test_message.apply(args=["hello"])

        self.assertIn("hello", captured.output[0])
