import os
import tempfile
import unittest

from main_file import LOG_BACKUP_COUNT, rotate_logs_on_start


class LoggingRotationTests(unittest.TestCase):
    def test_rotate_logs_on_start_keeps_current_plus_four_old_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "crosshud.log")
            with open(log_file, "w", encoding="utf-8") as f:
                f.write("current")
            for index in range(1, LOG_BACKUP_COUNT + 1):
                with open(f"{log_file}.{index}", "w", encoding="utf-8") as f:
                    f.write(f"old-{index}")

            rotate_logs_on_start(log_file)

            self.assertFalse(os.path.exists(log_file))
            with open(f"{log_file}.1", encoding="utf-8") as f:
                self.assertEqual(f.read(), "current")
            with open(f"{log_file}.2", encoding="utf-8") as f:
                self.assertEqual(f.read(), "old-1")
            with open(f"{log_file}.4", encoding="utf-8") as f:
                self.assertEqual(f.read(), "old-3")
            self.assertFalse(os.path.exists(f"{log_file}.5"))


if __name__ == "__main__":
    unittest.main()
