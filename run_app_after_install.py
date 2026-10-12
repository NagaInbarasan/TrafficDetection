import subprocess
import time
import sys

def check_installation():
    try:
        import ultralytics
        return True
    except ImportError:
        return False

print("Waiting for ultralytics to be installed...")
while not check_installation():
    time.sleep(5)

print("Dependencies are ready. Starting Flask app...")
subprocess.run([sys.executable, "app.py"])
