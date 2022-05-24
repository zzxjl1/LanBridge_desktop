import json
import os
import shutil
import time

import requests
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from connections import clients_lan
from toolutils import getpath
from ui import ui

os.chdir(getpath())
sync_path = "./sync_folder"


class conflict_solver():
    def __init__(self):
        self.data = []

    def maintenance(self):
        now = time.time()
        self.data = [i for i in self.data if now < i[0]]

    def add(self, path, duration=1):
        self.maintenance()
        self.data.append([time.time() + duration, path])
        self.data.append([time.time() + duration, sync_path])

    def set_duration(self, path, duration=1):
        for i in self.data:
            if i[1] == path:
                i[0] = time.time() + duration

    def is_conflict(self, path):
        self.maintenance()
        return path in [i[1] for i in self.data]


conflict_solver = conflict_solver()


def del_path(path):
    try:
        if os.path.isfile(path):
            os.remove(path)
        else:
            shutil.rmtree(path)
    except FileNotFoundError:
        pass


def normalize_path(path):
    return path.replace("\\", "/")


def broadcast_sync_folder_event(event_type, target):
    if conflict_solver.is_conflict(target):
        return
    clients_lan.broadcast(json.dumps({
        "action": "sync_folder_event",
        "event_type": event_type,
        "target": target
    }, ensure_ascii=False))


class MyHandler(FileSystemEventHandler):
    """
    def on_any_event(self, event):
        print(event.event_type, event.src_path)
        pass
    """

    def on_created(self, event):
        path = normalize_path(event.src_path)
        print("on_created", path)
        broadcast_sync_folder_event("on_created", path)

    def on_deleted(self, event):
        path = normalize_path(event.src_path)
        print("on_deleted", path)
        broadcast_sync_folder_event("on_deleted", path)

    def on_modified(self, event):
        path = normalize_path(event.src_path)
        print("on_modified", path)
        broadcast_sync_folder_event("on_modified", path)

    def on_moved(self, event):
        path = normalize_path(event.src_path)
        print("on_moved", path)
        broadcast_sync_folder_event("on_moved", path)


def get_sync_folder_structure():
    result = {"dirs": [], "files": []}
    for root, d, f in os.walk(sync_path):
        for name in d:
            path = os.path.join(root, name)
            result["dirs"].append({
                "root": normalize_path(root),
                "name": name,
                "path": normalize_path(path),
                # "last_modified_time":os.path.getmtime(path)
            })

        for name in f:
            path = os.path.join(root, name)
            result["files"].append({
                "root": normalize_path(root),
                "name": name,
                "path": normalize_path(path),
                "last_modified_time": os.path.getmtime(path)
            })

    # print(result)
    return result


def get_remote_sync_folder_structure(ip):
    try:
        result = requests.get("http://{}:{}/api/sync_folder_structure".format(ip, 8000))
        result = json.loads(result.text)
        return result
    except Exception as e:
        print("get_remote_sync_folder_structure failed", e)
        return


def download_from_remote(ip, path):
    conflict_solver.add(path, duration=float("inf"))
    r = requests.get("http://{}:{}/api/sync_file_download?path={}".format(ip, 8000, path))
    with open(path, 'wb') as f:
        f.write(r.content)
        f.close()
    conflict_solver.set_duration(path)


from toolutils import debounce


@debounce(0.5)
def resync(ip, force_self_del=False):  # 和其他机器比较并同步自己没有的文件和过期的文件
    # t={'dirs': [{'root': './sync_folder', 'name': '1', 'path': './sync_folder\\1'}, {'root': './sync_folder\\1', 'name': '1', 'path': './sync_folder\\1\\1'}, {'root': './sync_folder\\1', 'name': '2', 'path': './sync_folder\\1\\2'}], 'files': [{'root': './sync_folder\\1', 'name': '新建文本文档.txt', 'path': './sync_folder\\1\\新建文本文档.txt', 'last_modified_time': 6640962900.59571}, {'root': './sync_folder\\1\\1', 'name': '新建文本文档.txt', 'path': './sync_folder\\1\\1\\新建文本文档.txt', 'last_modified_time': 1640962894.9088137}]}
    print("sync_folder is doing its job!")
    t = get_remote_sync_folder_structure(ip)
    if not t:
        return
    for item in t["dirs"]:
        path = item["path"]
        if not os.path.exists(path):
            print(item, "对面有自己没有")
            conflict_solver.add(path)
            os.makedirs(path)
        elif not os.path.isdir(path):
            print(item, "不是目录")
            conflict_solver.add(path)
            del_path(path)
            os.makedirs(path)
    for item in t["files"]:
        path = item["path"]
        if not os.path.exists(path):
            print(item, "对面有自己没有")
            download_from_remote(ip, path)
        elif not os.path.isfile(path):
            print(item, "不是文件")
            del_path(path)
            download_from_remote(ip, path)
        elif os.path.getmtime(path) < item["last_modified_time"]:
            print(item, "是旧文件")
            # del_path(path)
            download_from_remote(ip, path)

    if force_self_del:
        result = get_sync_folder_structure()
        for item in result["dirs"]:
            if item not in t["dirs"]:
                print(item, "自己有对面没有")
                del_path(item["path"])
        remote_file_paths = [i["path"] for i in t["files"]]
        for item in result["files"]:
            if item["path"] not in remote_file_paths:
                print(item, "自己有对面没有")
                del_path(item["path"])
    print("sync_folder job done!")


def sync_folder_event_handler(msg, ip):
    path = msg["target"]
    conflict_solver.add(path)
    if msg["event_type"] == "on_deleted":
        del_path(path)
    elif msg["event_type"] == "on_moved":
        del_path(path)
        resync(ip)
    else:
        resync(ip, force_self_del=True)
    ui.show_toast("共享文件夹同步完成！")


def start_sync_folder_observer():
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, sync_path, recursive=True)
    observer.start()
