import copy
import json
import logging
import os
import re
import shutil
from typing import Any, Dict, List, Optional, Tuple
from threading import Lock

from app_metadata import APP_DATA_DIR_NAME, APP_VERSION, LEGACY_APP_DATA_DIR_NAMES
from hotkeys import HOTKEY_NAMES


class SettingsManager:
    CURRENT_VERSION = APP_VERSION
    MAX_CUSTOM_PIXELS = 101 * 101
    HOTKEYS = set(HOTKEY_NAMES)
    COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

    DEFAULT_SETTINGS = {
        'version': CURRENT_VERSION,
        'enabled': True,
        'size': 20.0,
        'thickness': 2.0,
        'gap': 4.0,
        'color': '#00FF00',
        'opacity': 1.0,
        'outline_enabled': False,
        'outline_color': '#000000',
        'outline_width': 1.0,
        'rmb_hide_mode': 'hold',
        'rainbow_mode': False,
        'pixel_perfect': False,
        'custom_pixels': [],
        'center_dot': False,
        'center_dot_size': 2.0,
        'center_dot_color': '#FF0000',
        'dynamic_color': False,
        'screen_width': 1920,
        'screen_height': 1080,
        'overlay_size': 512,
        'hotkey': 'Insert',
        'autostart': False,
        'start_minimized': False,
        'check_updates': True
    }

    BOOL_KEYS = {
        'enabled', 'outline_enabled', 'rainbow_mode', 'pixel_perfect',
        'center_dot', 'dynamic_color', 'autostart', 'start_minimized',
        'check_updates'
    }
    COLOR_KEYS = {'color', 'outline_color', 'center_dot_color'}
    ENUMS = {
        'rmb_hide_mode': {'disabled', 'hold', 'toggle'},
        'hotkey': HOTKEYS,
    }
    NUMBER_RULES = {
        'size': (1.0, 100.0, float),
        'thickness': (1.0, 20.0, float),
        'gap': (0.0, 50.0, float),
        'opacity': (0.01, 1.0, float),
        'outline_width': (0.0, 5.0, float),
        'center_dot_size': (1.0, 10.0, float),
        'screen_width': (800, 7680, int),
        'screen_height': (600, 4320, int),
        'overlay_size': (64, 1024, int),
    }

    def __init__(self, settings_file: Optional[str] = None):
        self.lock = Lock()
        self.settings = copy.deepcopy(self.DEFAULT_SETTINGS)
        self.settings['custom_templates'] = []
        self._warnings: List[str] = []
        self._saved_custom_pixels_snapshot: List[List[Any]] = []
        self._saved_settings_snapshot: Dict[str, Any] = {}
        home_dir = os.path.expanduser("~")
        self.app_data_dir = os.path.join(home_dir, APP_DATA_DIR_NAME)
        self.profiles_dir = os.path.join(self.app_data_dir, "profiles")
        self.is_profile_load = bool(settings_file)
        if self.is_profile_load:
            self.settings_file = settings_file
            self.load_from_file(settings_file)
        else:
            self._migrate_legacy_app_data(home_dir)
            os.makedirs(self.app_data_dir, exist_ok=True)
            os.makedirs(self.profiles_dir, exist_ok=True)
            self.settings_file = os.path.join(self.app_data_dir, 'settings.json')
            self._initialize_settings()

    def _migrate_legacy_app_data(self, home_dir: str) -> None:
        for dirname in LEGACY_APP_DATA_DIR_NAMES:
            legacy_dir = os.path.join(home_dir, dirname)
            if not os.path.isdir(legacy_dir):
                continue
            try:
                if not os.path.exists(self.app_data_dir):
                    shutil.copytree(legacy_dir, self.app_data_dir)
                else:
                    self._merge_legacy_app_data(legacy_dir)
                logging.info("Migrated app data from %s to %s", legacy_dir, self.app_data_dir)
            except Exception:
                logging.exception("Failed to migrate app data from %s", legacy_dir)
            return

    def _merge_legacy_app_data(self, legacy_dir: str) -> None:
        os.makedirs(self.app_data_dir, exist_ok=True)
        legacy_settings = os.path.join(legacy_dir, "settings.json")
        current_settings = os.path.join(self.app_data_dir, "settings.json")
        settings_replaced = False
        if os.path.exists(legacy_settings) and (
            not os.path.exists(current_settings)
            or self._should_replace_with_legacy_settings(current_settings, legacy_settings)
        ):
            shutil.copy2(legacy_settings, current_settings)
            settings_replaced = True

        legacy_client_id = os.path.join(legacy_dir, "client_id.txt")
        current_client_id = os.path.join(self.app_data_dir, "client_id.txt")
        if os.path.exists(legacy_client_id) and (settings_replaced or not os.path.exists(current_client_id)):
            shutil.copy2(legacy_client_id, current_client_id)

        self._copy_missing_tree(os.path.join(legacy_dir, "profiles"), os.path.join(self.app_data_dir, "profiles"))
        self._copy_missing_tree(
            os.path.join(legacy_dir, "support_reports"),
            os.path.join(self.app_data_dir, "support_reports"),
        )

    def _copy_missing_tree(self, source_dir: str, target_dir: str) -> None:
        if not os.path.isdir(source_dir):
            return
        for root, _, files in os.walk(source_dir):
            rel_root = os.path.relpath(root, source_dir)
            target_root = target_dir if rel_root == "." else os.path.join(target_dir, rel_root)
            os.makedirs(target_root, exist_ok=True)
            for filename in files:
                source_path = os.path.join(root, filename)
                target_path = os.path.join(target_root, filename)
                if not os.path.exists(target_path):
                    shutil.copy2(source_path, target_path)

    def _should_replace_with_legacy_settings(self, current_path: str, legacy_path: str) -> bool:
        try:
            with open(current_path, "r", encoding="utf-8") as f:
                current = json.load(f)
            with open(legacy_path, "r", encoding="utf-8") as f:
                legacy = json.load(f)
        except Exception:
            return False
        return not self._settings_has_user_data(current) and self._settings_has_user_data(legacy)

    def _settings_has_user_data(self, data: Any) -> bool:
        if not isinstance(data, dict):
            return False
        for key, default in self.DEFAULT_SETTINGS.items():
            if key == "version":
                continue
            if key in data and data[key] != default:
                return True
        return False

    def _warn(self, message: str) -> None:
        logging.warning(message)
        self._warnings.append(message)

    def consume_warnings(self) -> List[str]:
        with self.lock:
            warnings = list(self._warnings)
            self._warnings.clear()
        return warnings

    def _initialize_settings(self):
        if os.path.exists(self.settings_file):
            self.load_settings()
        else:
            self._try_migrate_old_config()
            self.save_settings()
        self.load_templates_from_disk()

    def _try_migrate_old_config(self):
        old_filename = 'crosshair_settings.json'
        possible_paths = [os.path.join(self.app_data_dir, old_filename), old_filename]
        found_old_config = next((p for p in possible_paths if os.path.exists(p)), None)
        if not found_old_config:
            return

        try:
            with open(found_old_config, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
            normalized = self._normalize_settings(old_data, partial=True, source="старый конфиг")
            with self.lock:
                self.settings.update(normalized)
                self._saved_custom_pixels_snapshot = copy.deepcopy(self.settings.get('custom_pixels', []))
                self._saved_settings_snapshot = self._persistable_settings_snapshot()
            os.rename(found_old_config, found_old_config + ".old")
        except Exception:
            logging.exception("Failed to migrate old config")

    def load_settings(self) -> bool:
        try:
            if not os.path.exists(self.settings_file):
                return False
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            normalized = self._normalize_settings(data, partial=False, source="settings.json")
            with self.lock:
                templates = self.settings.get('custom_templates', [])
                self.settings = normalized
                self.settings['custom_templates'] = templates
                self._saved_custom_pixels_snapshot = copy.deepcopy(self.settings.get('custom_pixels', []))
                self._saved_settings_snapshot = self._persistable_settings_snapshot()
            return True
        except Exception:
            logging.exception("Failed to load settings")
            self._warn("Не удалось прочитать настройки. Применены безопасные значения по умолчанию.")
            return False

    def load_templates_from_disk(self):
        templates = []
        if os.path.exists(self.profiles_dir):
            for filename in sorted(os.listdir(self.profiles_dir)):
                if not filename.endswith(".json"):
                    continue
                filepath = os.path.join(self.profiles_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        t_data = json.load(f)
                    name = t_data.get('name')
                    pixels = self._validate_custom_pixels(t_data.get('pixels', []), f"шаблон {filename}")
                    if isinstance(name, str) and name.strip():
                        templates.append({'name': name.strip(), 'pixels': pixels, '_filename': filename})
                except Exception:
                    logging.exception("Failed to load template: %s", filepath)
        with self.lock:
            self.settings['custom_templates'] = templates

    def save_template(self, template_data: Dict[str, Any]) -> str:
        name = template_data.get('name', 'Unnamed')
        if not isinstance(name, str):
            name = 'Unnamed'
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        if not safe_name:
            safe_name = "template"

        raw_filename = template_data.get('_filename')
        filename = os.path.basename(raw_filename) if isinstance(raw_filename, str) else f"{safe_name}.json"
        if not filename.endswith(".json"):
            filename += ".json"
        filepath = self._profile_path(filename)
        save_data = {"name": name, "pixels": self._validate_custom_pixels(template_data.get('pixels', []), "шаблон")}
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            return filename
        except Exception:
            logging.exception("Failed to save template: %s", filepath)
            return ""

    def delete_template(self, template_data: Dict[str, Any]) -> bool:
        filename = template_data.get('_filename')
        if not isinstance(filename, str) or not filename:
            return False
        filepath = self._profile_path(os.path.basename(filename))
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                return True
            except Exception:
                logging.exception("Failed to delete template: %s", filepath)
        return False

    def save_settings(self, include_custom_pixels: bool = False) -> bool:
        if self.is_profile_load:
            return True

        try:
            with self.lock:
                settings_data = {
                    k: copy.deepcopy(v)
                    for k, v in self.settings.items()
                    if k != 'custom_templates'
                }
                if include_custom_pixels:
                    custom_pixels_to_save = copy.deepcopy(self.settings.get('custom_pixels', []))
                else:
                    custom_pixels_to_save = copy.deepcopy(self._saved_custom_pixels_snapshot)
                if custom_pixels_to_save:
                    settings_data['custom_pixels'] = custom_pixels_to_save
                else:
                    settings_data.pop('custom_pixels', None)
                settings_data['version'] = self.CURRENT_VERSION
                saved_snapshot = copy.deepcopy(settings_data)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=2, ensure_ascii=False)
            if include_custom_pixels:
                with self.lock:
                    self._saved_custom_pixels_snapshot = copy.deepcopy(self.settings.get('custom_pixels', []))
            with self.lock:
                self._saved_settings_snapshot = saved_snapshot
            return True
        except Exception:
            logging.exception("Failed to save settings")
            return False

    def load_from_file(self, filepath: str) -> bool:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
            normalized = self._normalize_settings(loaded_settings, partial=True, source=os.path.basename(filepath))
            with self.lock:
                self.settings.update(normalized)
                if 'custom_pixels' in normalized:
                    self._saved_custom_pixels_snapshot = copy.deepcopy(normalized['custom_pixels'])
                self._saved_settings_snapshot = self._persistable_settings_snapshot()
            return True
        except Exception:
            logging.exception("Failed to load settings from file: %s", filepath)
            self._warn("Не удалось загрузить профиль. Проверьте формат файла.")
            return False

    def set_resolution(self, width: int, height: int) -> bool:
        if not (800 <= width <= 7680 and 600 <= height <= 4320):
            return False
        with self.lock:
            self.settings['screen_width'] = int(width)
            self.settings['screen_height'] = int(height)
        return True

    def has_unsaved_custom_pixels(self) -> bool:
        with self.lock:
            return self.settings.get('custom_pixels', []) != self._saved_custom_pixels_snapshot

    def has_unsaved_settings(self) -> bool:
        with self.lock:
            return self._persistable_settings_snapshot() != self._saved_settings_snapshot

    def get(self, key: str, default: Any = None) -> Any:
        with self.lock:
            return self.settings.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        if key not in self.DEFAULT_SETTINGS:
            self._warn(f"runtime: неизвестная настройка '{key}' отклонена.")
            return False
        normalized = self._normalize_settings({key: value}, partial=True, source="runtime")
        if key not in normalized:
            return False
        value = normalized[key]
        with self.lock:
            self.settings[key] = value
        return True

    def _profile_path(self, filename: str) -> str:
        os.makedirs(self.profiles_dir, exist_ok=True)
        return os.path.join(self.profiles_dir, filename)

    def _persistable_settings_snapshot(self) -> Dict[str, Any]:
        snapshot = {
            k: copy.deepcopy(v)
            for k, v in self.settings.items()
            if k != 'custom_templates'
        }
        if not snapshot.get('custom_pixels'):
            snapshot.pop('custom_pixels', None)
        snapshot['version'] = self.CURRENT_VERSION
        return snapshot

    def _normalize_settings(self, data: Any, *, partial: bool, source: str) -> Dict[str, Any]:
        if not isinstance(data, dict):
            self._warn(f"{source}: поврежденный формат настроек. Применены безопасные значения.")
            return {} if partial else copy.deepcopy(self.DEFAULT_SETTINGS)

        normalized = {} if partial else copy.deepcopy(self.DEFAULT_SETTINGS)
        for key, default in self.DEFAULT_SETTINGS.items():
            if key == 'version':
                normalized[key] = self.CURRENT_VERSION
                continue
            if key not in data:
                continue
            normalized[key] = self._normalize_value(key, data[key], default, source)

        if 'custom_pixels' in normalized:
            normalized['custom_pixels'] = self._validate_custom_pixels(normalized['custom_pixels'], source)
        return normalized

    def _normalize_value(self, key: str, value: Any, default: Any, source: str) -> Any:
        if key in self.BOOL_KEYS:
            if isinstance(value, bool):
                return value
            self._warn(f"{source}: поле '{key}' повреждено, применено значение по умолчанию.")
            return default

        if key in self.COLOR_KEYS:
            if isinstance(value, str) and self.COLOR_RE.match(value):
                return value.upper()
            self._warn(f"{source}: цвет '{key}' поврежден, применено значение по умолчанию.")
            return default

        if key in self.ENUMS:
            if isinstance(value, str) and value in self.ENUMS[key]:
                return value
            self._warn(f"{source}: поле '{key}' повреждено, применено значение по умолчанию.")
            return default

        if key in self.NUMBER_RULES:
            min_v, max_v, caster = self.NUMBER_RULES[key]
            if isinstance(value, bool):
                self._warn(f"{source}: поле '{key}' повреждено, применено значение по умолчанию.")
                return default
            try:
                num = caster(value)
            except (TypeError, ValueError):
                self._warn(f"{source}: поле '{key}' повреждено, применено значение по умолчанию.")
                return default
            if num < min_v or num > max_v:
                self._warn(f"{source}: поле '{key}' вне диапазона, значение ограничено.")
                num = max(min_v, min(max_v, num))
            return num

        if key == 'custom_pixels':
            return value

        return value

    def _validate_custom_pixels(self, pixels: Any, source: str) -> List[List[Any]]:
        if not isinstance(pixels, list):
            self._warn(f"{source}: пиксельный прицел поврежден, он сброшен.")
            return []

        normalized = []
        seen = set()
        for item in pixels[:self.MAX_CUSTOM_PIXELS]:
            if not isinstance(item, (list, tuple)) or len(item) != 3:
                continue
            px, py, color = item
            if isinstance(px, bool) or isinstance(py, bool):
                continue
            try:
                px = int(px)
                py = int(py)
            except (TypeError, ValueError):
                continue
            if not (-50 <= px <= 50 and -50 <= py <= 50):
                continue
            if not isinstance(color, str) or not self.COLOR_RE.match(color):
                continue
            if (px, py) in seen:
                continue
            seen.add((px, py))
            normalized.append([px, py, color.upper()])

        if len(pixels) > self.MAX_CUSTOM_PIXELS:
            self._warn(f"{source}: пиксельный прицел слишком большой, лишние точки отброшены.")
        if len(normalized) != len(pixels[:self.MAX_CUSTOM_PIXELS]):
            self._warn(f"{source}: часть точек пиксельного прицела была исправлена или отброшена.")
        return normalized
