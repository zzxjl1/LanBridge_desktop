import json
import threading
import time

import eel
import pyperclip

from connections import clients_lan
from settings import settings
from ui import ui


def broadcast_clipboard_update(text):
    if not text or text == remote_data:
        return
    ui.show_toast("已发送剪切板同步广播！")
    clients_lan.broadcast(json.dumps({
        "action": "clipboard_update",
        "data": text
    }))


remote_data = None
is_running = False


def set_clipboard(text):
    if not settings.clipboard_share_switch:
        return
    global remote_data
    remote_data = text
    ui.show_toast("剪切板同步完成！")
    pyperclip.copy(text)


def clipboard_deamon():
    global text
    last = pyperclip.paste()
    while settings.clipboard_share_switch:
        time.sleep(0.5)
        text = pyperclip.paste()
        if not text:
            continue
        if last != text:
            last = text
            print(text)
            broadcast_clipboard_update(text)


def is_clipboard_deamon_running():
    return settings.clipboard_share_switch


def clipboard_share_start():
    global is_running
    if is_running:
        return
    settings.set_clipboard_share_switch(True)
    try:
        threading.Thread(target=clipboard_deamon).start()
        print("clipboard_deamon started")
        ui.set_clipboard_share_switch(True)
        is_running = True
        eel.update_clipboard_share_switch()
    except Exception as e:
        ui.show_error("共享剪切板时出错", "clipboard not supported!")
        clipboard_share_stop()


def clipboard_share_stop():
    global is_running
    settings.set_clipboard_share_switch(False)
    print("clipboard_deamon ended")
    ui.set_clipboard_share_switch(False)
    is_running = False
    eel.update_clipboard_share_switch()
