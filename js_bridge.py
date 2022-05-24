import eel,json,os,sys
from toolutils import safe_serialize,show_folder
import webbrowser,threading

@eel.expose
def get_all_lan_clients():
    from connections import clients_lan
    return json.dumps(safe_serialize(clients_lan.data))
    
@eel.expose
def show_file_explorer(ip):
    url="http://{}:{}/file_explorer".format(ip,8000)
    webbrowser.open(url, new=1, autoraise=True)

@eel.expose
def start_keyboard_mouse_cast(ip):
    from plugins.keyboard_mouse import start
    start(ip)
    
@eel.expose
def ping():
    return "pong"

@eel.expose
def show_sync_folder():
    show_folder("sync_folder")
    
@eel.expose
def power_management(ip,action):
    def get():
        import requests
        requests.get("http://{}:{}/api/{}".format(ip,8000,action))
    threading.Thread(target=get).start()
    
@eel.expose
def is_soundwire_running():
    from plugins.soundwire import is_soundwire_host_running
    return is_soundwire_host_running()

@eel.expose
def toggle_soundwire(t):
    from plugins.soundwire import start_soundwire_host,stop_soundwire_host
    if t:
        start_soundwire_host()
    else:
        stop_soundwire_host()

@eel.expose
def set_soundwire_target(result):
    from settings import settings
    t = json.loads(result)
    settings.set_soundwire_target(t)

@eel.expose
def get_soundwire_target():
    from settings import settings
    return json.dumps(settings.soundwire_target)
    
@eel.expose
def is_clipboard_share_running():
    from plugins.clipboard import is_clipboard_deamon_running
    return is_clipboard_deamon_running()

@eel.expose
def toggle_clipboard_share(t):
    from plugins.clipboard import clipboard_share_start,clipboard_share_stop
    if t:
        clipboard_share_start()
    else:
        clipboard_share_stop()

@eel.expose
def is_undisturb_on():
    from ui import ui
    return ui.is_undisturb_mode_on()
@eel.expose
def toggle_undisturb_mode(t):
    from ui import ui
    ui.toggle_undisturb_mode(t)
    
@eel.expose
def send_file(ip):
    from plugins.file_transmit import send_to
    threading.Thread(target=send_to,args=(ip,)).start()

@eel.expose
def find_my_device(ip):
    def get():
        import requests
        requests.get("http://{}:{}/api/{}".format(ip,8000,"find_my_device"))
    threading.Thread(target=get).start()
    
@eel.expose
def get_alias(mac_addr):
    from db.api import get_hostname_alias
    return get_hostname_alias(mac_addr)

@eel.expose
def set_alias(mac_addr,alias):
    from db.api import set_hostname_alias
    set_hostname_alias(mac_addr,alias)

    
