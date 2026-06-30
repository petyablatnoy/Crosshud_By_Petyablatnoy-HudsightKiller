import os
import shutil
import subprocess
import sys
import venv


BUILD_VENV = ".venv-build"
APP_NAME = "CrossHud_By_PetyaBlatnoy"


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
        '--version-file=version_info.txt',
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
        py = ensure_build_env()
        build(py)
        sign()
        pack()
    except Exception as exc:
        print(f"Build failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
