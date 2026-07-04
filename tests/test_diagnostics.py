import os
import tempfile
import unittest
from unittest import mock

from diagnostics import DiagnosticService


class DummySettings:
    def get(self, key):
        return {"screen_width": 2560, "screen_height": 1440}[key]


class DiagnosticServiceTests(unittest.TestCase):
    def test_client_id_is_generated_once_and_reused(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = DiagnosticService(
                temp_dir,
                os.path.join(temp_dir, "settings.json"),
                os.path.join(temp_dir, "crosshud.log"),
            )

            first = service.client_id()
            second = DiagnosticService(temp_dir, "", "").client_id()

            self.assertEqual(first, second)
            self.assertEqual(len(first), 36)

    def test_report_contains_support_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = DiagnosticService(
                temp_dir,
                os.path.join(temp_dir, "settings.json"),
                os.path.join(temp_dir, "crosshud.log"),
                DummySettings(),
            )

            report = service.report_text()

            self.assertIn("Версия:", report)
            self.assertIn("UID:", report)
            self.assertIn("Windows:", report)
            self.assertIn("Видеокарта:", report)
            self.assertIn("Драйвер GPU:", report)
            self.assertIn("Дисплей:", report)
            self.assertIn("Разрешение оверлея: 2560x1440", report)
            self.assertIn("Логи:", report)

    def test_video_info_is_cached_and_tolerates_missing_cim(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = DiagnosticService(temp_dir, "", "")

            with mock.patch("diagnostics.subprocess.run", side_effect=FileNotFoundError):
                self.assertEqual(service._video_names(), "недоступно")
                self.assertEqual(service._video_names(), "недоступно")

            self.assertEqual(service._video_info_cache, [])


if __name__ == "__main__":
    unittest.main()
