import os
import shutil
import subprocess
import sys
import venv

from app_metadata import APP_FILE_VERSION, APP_NAME, APP_VERSION, APP_VERSION_TUPLE, FILE_DESCRIPTION


BUILD_VENV = ".venv-build"
VERSION_INFO_FILE = "version_info.txt"
INSTALLER_VERSION_FILE = "installer_version.nsh"


def build_python():
    if os.name == "nt":
        return os.path.join(BUILD_VENV, "Scripts", "python.exe")
    return os.path.join(BUILD_VENV, "bin", "python")


def ensure_build_env():
    py = build_python()
    if not os.path.exists(py):
        venv.EnvBuilder(with_pip=True, clear=False).create(BUILD_VENV)
    subprocess.run([py, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([py, "-m", "pip", "install", "-r", "requirements-build.txt"], check=True)
    return py


def clean():
    for path in ["dist", "build"]:
        if os.path.isdir(path):
            shutil.rmtree(path)


def write_build_metadata():
    filevers = ",".join(str(part) for part in APP_VERSION_TUPLE)
    with open(VERSION_INFO_FILE, "w", encoding="utf-8") as f:
        f.write(
            "VSVersionInfo(\n"
            f"  ffi=FixedFileInfo(filevers=({filevers}), prodvers=({filevers}),\n"
            "    mask=0x3f, flags=0x0, OS=0x4, fileType=0x1, subtype=0x0, date=(0, 0)),\n"
            "  kids=[StringFileInfo([StringTable(u'040904B0', [\n"
            f"    StringStruct(u'FileDescription', u'{FILE_DESCRIPTION}'),\n"
            f"    StringStruct(u'FileVersion', u'{APP_FILE_VERSION}'),\n"
            f"    StringStruct(u'ProductName', u'{APP_NAME}'),\n"
            f"    StringStruct(u'ProductVersion', u'{APP_FILE_VERSION}')])]),\n"
            "  VarFileInfo([VarStruct(u'Translation', [1033, 1200])])])\n"
        )
    with open(INSTALLER_VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(
            f'!define APP_NAME "{APP_NAME}"\n'
            f'!define APP_VERSION "{APP_VERSION}"\n'
            f'!define EXE_NAME "{APP_NAME}.exe"\n'
        )


def build(py):
    cmd = [
        py,
        '-m',
        'PyInstaller',
        '--name=' + APP_NAME,
        '--onedir',
        '--windowed',
        '--noconfirm',
        '--clean',
        '--collect-binaries=PySide6',
        '--uac-uiaccess',
        '--icon=icon.ico',
        f'--version-file={VERSION_INFO_FILE}',
        '--add-data=icon.ico;.',
        '--add-data=qml;qml',
        '--add-data=assets;assets',
        '--hidden-import=PySide6',
        '--hidden-import=PySide6.QtQml',
        '--hidden-import=PySide6.QtQuick',
        '--hidden-import=PySide6.QtQuickControls2',
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image',
        '--hidden-import=PIL.ImageDraw',
        'main_file.py'
    ]
    subprocess.run(cmd, check=True)
    dist_dir = os.path.join('dist', APP_NAME)
    if os.path.exists('icon.ico') and os.path.exists(dist_dir):
        shutil.copy('icon.ico', os.path.join(dist_dir, 'icon.ico'))


def sign():
    script = "sign_app.ps1"
    if not os.path.exists(script):
        raise FileNotFoundError(script)
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if not shell:
        raise FileNotFoundError("PowerShell executable not found")
    subprocess.run([shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script], check=True)


def pack():
    p86 = os.environ.get("ProgramFiles(x86)", "")
    p = os.environ.get("ProgramFiles", "")
    makensis = None
    for path in [os.path.join(p86, "NSIS", "makensis.exe"), os.path.join(p, "NSIS", "makensis.exe")]:
        if os.path.exists(path):
            makensis = path
            break
    if not makensis:
        raise FileNotFoundError("NSIS makensis.exe not found")
    subprocess.run([makensis, "/INPUTCHARSET", "UTF8", "installer.nsi"], check=True)


def main():
    try:
        clean()
        write_build_metadata()
        py = ensure_build_env()
        build(py)
        sign()
        pack()
    except Exception as exc:
        print(f"Build failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
