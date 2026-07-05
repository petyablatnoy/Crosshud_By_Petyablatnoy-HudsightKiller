APP_NAME = "CrossHud"
APP_DISPLAY_NAME = "CrossHud"
APP_VERSION = "4.0.2"
APP_VERSION_TUPLE = (4, 0, 2, 0)
APP_FILE_VERSION = ".".join(str(part) for part in APP_VERSION_TUPLE)
APP_USER_MODEL_ID = f"PetyaBlatnoy.CrossHud.App.{APP_VERSION}"
SINGLE_INSTANCE_SERVER_NAME = f"{APP_NAME}_{APP_VERSION}"
APP_DATA_DIR_NAME = "CrossHud"
LEGACY_APP_DATA_DIR_NAMES = ("CrossHud_By_PetyaBlatnoy",)

PROJECT_OWNER = "petyablatnoy"
PROJECT_REPO = "crosshud"
PROJECT_URL = f"https://github.com/{PROJECT_OWNER}/{PROJECT_REPO}"
UPDATE_API_URL = f"https://api.github.com/repos/{PROJECT_OWNER}/{PROJECT_REPO}/releases/latest"
UPDATE_RELEASES_PATH = f"/{PROJECT_OWNER}/{PROJECT_REPO}/releases/"
LEGACY_UPDATE_RELEASES_PATHS = ("/petyablatnoy/Crosshud_By_Petyablatnoy-HudsightKiller/releases/",)

FILE_DESCRIPTION = f"{APP_NAME} - Прицел-оверлей"
