import subprocess
import time
import sys

try:
    process = subprocess.Popen(
        [sys.executable, "main_file.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    time.sleep(5)
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
    stdout, stderr = process.communicate()
    print(stdout)
    print(stderr)
except Exception as e:
    pass