import json,os,shutil,threading,asyncio,zlib,queue
from connections import clients_lan
from plugins.sync_folder import sync_folder_event_handler
from plugins.soundwire import add_to_pcm_queue,is_soundwire_client_running,start_soundwire_client,get_mode,set_mode,handle_conflict
from plugins.clipboard import set_clipboard
from plugins.battery import parse_change
from plugins.keyboard_mouse import parse_remote_data


def worker(msg,ip):
    """
    if type(msg) is bytes:
        pcm_data = zlib.decompress(msg).decode('utf-8')
        add_to_pcm_queue(json.loads(pcm_data))
        return
    """
    msg = json.loads(msg)
    if msg["action"]=="soundwire_pcm":
        if msg["mode"]!=get_mode():
            set_mode(msg["mode"])
        add_to_pcm_queue(msg["data"])
        if not is_soundwire_client_running():
            start_soundwire_client()
    #    handle_conflict()
    elif msg["action"]=="keyboard_mouse_event":
        parse_remote_data(msg)
    elif msg["action"]=="sync_folder_event":
        sync_folder_event_handler(msg,ip)
    elif msg["action"]=="soundwire_broadcast_running_flag":
        handle_conflict(msg["targets"])
    elif msg["action"]=="clipboard_update":
        set_clipboard(msg["data"])
    elif msg["action"]=="battery_status_update":
        battery_status = clients_lan.get_battery_status(ip)
        if battery_status["has_battery"]:
            parse_change(ip,battery_status,msg["data"])
        clients_lan.set_battery_status(ip,msg["data"])
        
def ws_handler(msg,ip):
    try:
        worker(msg,ip)
    except Exception as e:
        import traceback
        traceback.print_exc()


async def consumer_handler(loop,websocket,ip):
    async for message in websocket:
        #print("recv:",message[:20])
        await loop.run_in_executor(None,ws_handler,message,ip)
async def producer_handler(loop,websocket,q):
    while True:
        #print("reading send queue")
        message = await loop.run_in_executor(None,q.get)
        #print("send:",message[:20])
        await websocket.send(message)
