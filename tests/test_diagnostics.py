import os
import tempfile
import unittest
import zipfile
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
            self.assertIn("CPU:", report)
            self.assertIn("RAM:", report)
            self.assertIn("Видеокарта:", report)
            self.assertIn("Драйвер GPU:", report)
            self.assertIn("Дисплей:", report)
            self.assertIn("Мониторы:", report)
            self.assertIn("Разрешение оверлея: 2560x1440", report)
            self.assertIn("Настройки прицела:", report)
            self.assertIn("Логи:", report)
            self.assertIn("@petyablatnoy", report)

    def test_support_archive_contains_system_info_and_last_logs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "crosshud.log")
            for suffix in ["", ".1", ".2", ".3", ".4", ".5"]:
                with open(log_file + suffix, "w", encoding="utf-8") as f:
                    f.write(f"log {suffix or 'current'}")
            service = DiagnosticService(temp_dir, os.path.join(temp_dir, "settings.json"), log_file)

            archive_path = service.create_support_archive()

            self.assertTrue(os.path.exists(archive_path))
            with zipfile.ZipFile(archive_path) as archive:
                names = archive.namelist()
            self.assertIn("system_info.txt", names)
            self.assertIn("system_info.json", names)
            self.assertEqual(len([name for name in names if name.startswith("logs/")]), 5)
            self.assertFalse(any(name.endswith("crosshud.log.5") for name in names))

    def test_video_info_is_cached_and_tolerates_missing_cim(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = DiagnosticService(temp_dir, "", "")

            with mock.patch("diagnostics.subprocess.run", side_effect=FileNotFoundError):
                self.assertEqual(service._video_names(), "недоступно")
                self.assertEqual(service._video_names(), "недоступно")

            self.assertEqual(service._video_info_cache, [])

    def test_rows_reuse_cached_system_queries(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = DiagnosticService(temp_dir, "", "")
            with mock.patch.object(service, "_powershell_json", return_value=None) as query:
                service.rows()
                service.rows()

            self.assertLessEqual(query.call_count, 2)


if __name__ == "__main__":
    unittest.main()
