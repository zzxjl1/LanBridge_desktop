import os
import platform
import subprocess

system = platform.system()

shutdown_mapping = {"Windows":"os.system('shutdown /s /f /t 0')",
                   "Linux":"os.system('systemctl poweroff -i')",
                   "Darwin":"""subprocess.call(['osascript', '-e','tell app "System Events" to shut down'])"""
                   }

restart_mapping = {"Windows":"os.system('shutdown /r /f /t 0')",
                   "Linux":"os.system('systemctl reboot -i')",
                   "Darwin":"""subprocess.call(['osascript', '-e','tell app "System Events" to restart'])"""
                   }

sleep_mapping = {"Windows":"os.system('shutdown /h /f')",
                   "Linux":"os.system('systemctl hibernate -i')",
                   "Darwin":"""subprocess.call(['osascript', '-e','tell app "System Events" to sleep'])"""
                   }
def shutdown():
    exec(shutdown_mapping[system])
def restart():
    exec(restart_mapping[system])
def hibernate():
    exec(sleep_mapping[system])

