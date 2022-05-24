from pynput import keyboard as keyboard_capture
import threading
import os, time, json
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController
from connections import clients_lan
from retrying import retry

os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (100, 100)
import pygame

keyboard = KeyboardController()
mouse = MouseController()
running = False
ip = None


def on_press(key):
    try:
        data = {"action": "keyboard_mouse_event", "type": "key_down", "data": key.char}
        clients_lan.send_to(ip, json.dumps(data))
    except AttributeError:
        data = {"action": "keyboard_mouse_event", "type": "key_down", "data": str(key)}
        clients_lan.send_to(ip, json.dumps(data))


def on_release(key):
    try:
        data = {"action": "keyboard_mouse_event", "type": "key_up", "data": key.char}
        clients_lan.send_to(ip, json.dumps(data))
    except AttributeError:
        data = {"action": "keyboard_mouse_event", "type": "key_up", "data": str(key)}
        clients_lan.send_to(ip, json.dumps(data))


def stop():
    global running
    running = False


def unfreeze():
    global keyboard_listener
    print("keyboard mouse mapping stops")
    keyboard_listener.stop()
    import eel
    eel.keyboard_mouse_cast_stopped()


def capture_on_exception(exception):
    import traceback
    traceback.print_exc()
    stop()
    unfreeze()
    pygame.display.quit()
    return False


@retry(retry_on_exception=capture_on_exception)
def capture():
    global keyboard_listener, running

    keyboard_listener = keyboard_capture.Listener(
        suppress=True,
        on_press=on_press,
        on_release=on_release)
    keyboard_listener.start()

    def hotkey_listener():
        global running
        with keyboard_capture.GlobalHotKeys({'w+u+f': stop}) as h:
            h.join()

    threading.Thread(target=hotkey_listener).start()

    pygame.init()
    pygame.display.set_mode((3, 3), pygame.NOFRAME)
    pygame.display.set_caption("LanBridge鼠标捕获")
    pygame.mouse.set_visible(False)
    pos_before_start = mouse.position
    mouse.position = list(map(int, os.environ['SDL_VIDEO_WINDOW_POS'].split(",")))
    mouse.click(Button.left, 1)
    running = True
    deamon_running = False
    print("keyboard mouse mapping start")
    clock = pygame.time.Clock()
    while running:
        clock.tick(360)  # fps
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEMOTION:
                pygame.event.set_grab(True)
                rel_pos = event.rel
                if rel_pos != (0, 0):
                    # print(rel_pos)
                    data = {"action": "keyboard_mouse_event", "type": "mouse_move", "rel_pos": rel_pos}
                    clients_lan.send_to(ip, json.dumps(data))

                if not deamon_running:
                    def deamon():
                        global running
                        while running:
                            if pygame.display.get_init() and not pygame.mouse.get_focused():
                                running = False
                            time.sleep(1)

                    threading.Thread(target=deamon).start()
                    deamon_running = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # print(event.button)
                data = {"action": "keyboard_mouse_event", "type": "mouse_down", "btn": event.button}
                clients_lan.send_to(ip, json.dumps(data))
            elif event.type == pygame.MOUSEBUTTONUP:
                # print(event.button)
                data = {"action": "keyboard_mouse_event", "type": "mouse_up", "btn": event.button}
                clients_lan.send_to(ip, json.dumps(data))
            elif event.type == pygame.MOUSEWHEEL:
                # print(event)
                data = {"action": "keyboard_mouse_event", "type": "mouse_scroll", "data": (event.x, event.y)}
                clients_lan.send_to(ip, json.dumps(data))
    unfreeze()
    pygame.display.quit()
    mouse.position = pos_before_start
    print("pygame quited")


def start(t):
    global ip
    ip = t
    threading.Thread(target=capture).start()


def parse_remote_data(t):
    mapping = {1: Button.left, 2: Button.middle, 3: Button.right}
    if t["type"] == "mouse_move":
        mouse.move(t["rel_pos"][0], t["rel_pos"][1])
    elif t["type"] == "mouse_down":
        btn_id = t["btn"]
        if btn_id in mapping:
            mouse.press(mapping[t["btn"]])
        elif btn_id == 4:
            mouse.scroll(0, 1)
        elif btn_id == 5:
            mouse.scroll(0, -1)
    elif t["type"] == "mouse_up":
        btn_id = t["btn"]
        if btn_id in mapping:
            mouse.release(mapping[t["btn"]])
        elif btn_id == 4:
            mouse.scroll(0, 1)
        elif btn_id == 5:
            mouse.scroll(0, -1)
    elif t["type"] == "mouse_scroll":
        mouse.scroll(t["data"][0], t["data"][1])
    elif t["type"] == "key_down":
        char = t["data"]
        if not char:
            return
        elif char.startswith("Key."):
            exec("keyboard.press({})".format(char))
        else:
            keyboard.press(char)
    elif t["type"] == "key_up":
        char = t["data"]
        if not char:
            return
        elif char.startswith("Key."):
            exec("keyboard.release({})".format(char))
        else:
            keyboard.release(char)
