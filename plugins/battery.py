import json
import threading
import time

import psutil
import requests

from connections import clients_lan
from ui import ui

battery = psutil.sensors_battery()


def get_remote_battery_status(ip):
    try:
        result = requests.get("http://{}:{}/api/battery_status".format(ip, 8000))
        result = json.loads(result.text)
        return result
    except Exception as e:
        print("get_remote_battery_status failed", e)
        return {"has_battery": False}


def parse_change(ip, old, new):
    if old == new:
        return
    if old["is_charging"] != new["is_charging"]:
        ui.show_toast(ip + ("接入电源" if new["is_charging"] else "正使用电池"))
    if old["percentage"] != new["percentage"]:
        print(ip, "battery percentage changed to", new["percentage"])
        if new["percentage"] < 20 and not new["is_charging"]:
            ui.show_toast("{} 电池电量低（{}%）".format(ip, new["percentage"]))


def convertTime(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return "%d:%02d:%02d" % (hours, minutes, seconds)


def get_battery_status():
    global battery
    battery = psutil.sensors_battery()
    if battery:
        # print("Battery percentage : ", battery.percent)
        # print("Power plugged in : ", battery.power_plugged)
        return (battery.percent, battery.power_plugged)
    else:
        return None


def battery_data():
    result = get_battery_status()
    if result:
        return {
            "has_battery": True,
            "percentage": result[0],
            "is_charging": result[1],
            "time_left": convertTime(battery.secsleft)
        }
    else:
        return {"has_battery": False}


def broadcast_battery_status():
    if not battery:
        return
    clients_lan.broadcast(json.dumps({
        "action": "battery_status_update",
        "data": battery_data()
    }))


def battery_deamon():
    last = get_battery_status()
    while True:
        time.sleep(1)
        now = get_battery_status()
        if last != now:
            last = now
            print("batterystatus change detected:", now)
            broadcast_battery_status()


def start_battery_deamon():
    if battery:
        print("battery_deamon started")
        threading.Thread(target=battery_deamon).start()
    else:
        print("battery not detected or not supported")
