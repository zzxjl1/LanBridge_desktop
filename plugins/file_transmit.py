import datetime
import os
import time

import requests
from retrying import retry

from toolutils import normalize_path, get_sys_info
from ui import ui

file_path = None
flag = time.time()


def set_path(path):
    global file_path
    file_path = path


def get_file_path(ip):
    global file_path, flag
    now = time.time()
    flag = now
    file_path = None
    ui.show_drag_file_dialog(ip)
    while file_path is None:
        time.sleep(0.1)
    if flag != now:
        return
    return file_path


from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor

throttle = 0


def my_callback(monitor):
    global throttle
    if time.time() - throttle < 0.1:
        return
    throttle = time.time()
    ui.set_file_transfer_progress_sending_label(uploading)
    ui.set_file_transfer_progress_count_label("第{}个，共{}个".format(count, total))
    ui.set_file_transfer_progress_file_progress(monitor.bytes_read / size * 100)
    ui.set_file_transfer_progress_total_progress(count / total * 100)


def post_file(tag, ip, root, path):
    global size, uploading, count
    fields = {}
    uploading = os.path.basename(path)
    if os.path.isfile(path):
        fields = {'type': 'file', 'tag': tag, 'root': root,
                  'file': (os.path.basename(path), open(path, 'rb'), 'text/plain')}
    elif os.path.isdir(path):
        fields = {'type': 'dir', 'tag': tag, 'root': root}
    else:
        return
    e = MultipartEncoder(fields)
    size = e.len
    m = MultipartEncoderMonitor(e, my_callback)
    r = requests.post('http://{}:8000/api/file_transmit'.format(ip), data=m, headers={'Content-Type': m.content_type})
    count += 1


def on_exception(exception):
    import traceback
    traceback.print_exc()
    ui.complete_file_transfer_progress()
    ui.show_error("文件传输时出错", str(exception))
    return False


@retry(retry_on_exception=on_exception)
def send_to(ip):
    global total, count
    path = get_file_path(ip)
    if not path:
        return
    print(path)
    count = 1
    total = 0
    for t in path:
        if os.path.isfile(t):
            total += 1
        elif os.path.isdir(t):
            for root, dirs, files in os.walk(t):
                total += len(dirs) + len(files)

    tag = "{} from {}".format(datetime.datetime.now().strftime("%Y_%m_%d %H_%M_%S"), get_sys_info()["hostname"])
    print("file transmit starts")
    ui.show_file_transfer_progress_dialog(ip)
    for t in path:
        if os.path.isfile(t):
            post_file(tag, ip, "", t)
        elif os.path.isdir(t):
            base = os.path.basename(t)
            for root, dirs, files in os.walk(t):
                for name in files:
                    post_file(tag, ip, normalize_path(os.path.relpath(root, os.path.dirname(t))),
                              normalize_path(os.path.join(root, name)))
                for name in dirs:
                    post_file(tag, ip, normalize_path(os.path.relpath(os.path.join(root, name), os.path.dirname(t))),
                              normalize_path(os.path.join(root, name)))
    requests.get("http://{}:8000/api/show_transmit_folder?tag={}".format(ip, tag))
    print("file transmit completed")
    ui.show_toast("文件传输完成！")
    ui.complete_file_transfer_progress()
