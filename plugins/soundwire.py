import json
import queue
import threading
import time
import numpy
import sounddevice as sd
from connections import clients_lan
assert numpy
from ui import ui
from retrying import retry
import eel
from settings import settings

soundwire_host_switch = False
soundwire_client_switch = False
mode = None


def now():
    return time.time()


def get_mode():
    global mode
    return mode


def set_mode(t="balance"):
    global mode, soundwire_host_switch, soundwire_client_switch
    temp = (soundwire_host_switch, soundwire_client_switch)
    soundwire_host_switch, soundwire_client_switch = False, False
    presets = {"quality": 4, "balance": 2, "performance": 1}
    if t not in presets.keys():
        return
    times = presets[t]
    sd.default.channels = 1
    sd.default.samplerate = 11025 * times
    sd.default.blocksize = 1024 * times
    sd.default.dtype = "int16"
    sd.default.latency = 0
    mode = t
    print("soundwire mode set to:", mode)
    sd.sleep(200)
    soundwire_host_switch, soundwire_client_switch = temp


set_mode()  # init


def broadcast_on_exception(exception):
    print(exception)
    stop_soundwire_host()

@retry(retry_on_exception=broadcast_on_exception)
def broadcast_start_flag():
    while soundwire_host_switch:
        msg = json.dumps({"action": "soundwire_broadcast_running_flag",
                          "targets":settings.soundwire_target
                          })
        clients_lan.broadcast(msg)
        time.sleep(1)
    

@retry(retry_on_exception=broadcast_on_exception)
def broadcast_pcm_data(pcm_data):
    msg = json.dumps({"action": "soundwire_pcm", "data": pcm_data, "mode": mode})
    clients_lan.broadcast(msg,target_ips = settings.soundwire_target)


def callback_host(indata, frames, time, status):
    if indata.max() > 0:
        t = indata.tolist()
        broadcast_pcm_data(t)


def soundwire_host():
    global soundwire_host_switch
    try:
        with sd.InputStream(callback=callback_host):
            print('SOUND WIRE HOST IS RUNNING')
            ui.show_toast("SOUNDWIRE 正在进行音频广播")
            ui.set_soundwire_host_switch(True)
            while True:
                if not soundwire_host_switch:
                    break
                sd.sleep(100)
            print('SOUND WIRE HOST DOWN')
            ui.show_toast("SOUNDWIRE 音频广播端已休眠")
            ui.set_soundwire_host_switch(False)
    except Exception as e:
        ui.show_error("SOUNDWIRE 音频广播时出错", str(e))
        stop_soundwire_host()


pcm_queue = queue.Queue(maxsize=2)


def add_to_pcm_queue(pcm_data):
    if pcm_queue.full():
        # pcm_queue.queue.clear()
        pcm_queue.get_nowait()
    pcm_queue.put_nowait(pcm_data)


client_last_frame_timestamp = now()


def callback_client(outdata, frames, time, status):
    global client_last_frame_timestamp
    if not pcm_queue.empty():
        data = pcm_queue.get_nowait()
        outdata[:] = data
        client_last_frame_timestamp = now()
    else:
        # outdata[:] =[[528], [504], [502], [478], [443], [467], [496], [489], [481], [479], [493], [515], [533], [550], [566], [570], [569], [576], [572], [551], [533], [534], [522], [498], [465], [417], [372], [317], [268], [222], [171], [159], [173], [197], [213], [212], [226], [234], [233], [241], [253], [257], [273], [302], [295], [287], [273], [254], [263], [265], [225], [178], [145], [89], [36], [8], [-40], [-108], [-142], [-142], [-131], [-125], [-142], [-158], [-143], [-135], [-142], [-134], [-129], [-117], [-97], [-89], [-83], [-104], [-124], [-86], [-47], [-54], [-79], [-74], [-64], [-81], [-108], [-137], [-165], [-199], [-250], [-259], [-258], [-292], [-300], [-301], [-335], [-363], [-362], [-356], [-355], [-348], [-335], [-310], [-306], [-310], [-287], [-273], [-275], [-273], [-269], [-272], [-293], [-331], [-373], [-419], [-470], [-505], [-523], [-538], [-545], [-543], [-541], [-543], [-549], [-547], [-545], [-580], [-593], [-561], [-551], [-579], [-591], [-593], [-606], [-618], [-626], [-630], [-644], [-673], [-692], [-695], [-719], [-764], [-769], [-756], [-764], [-760], [-743], [-733], [-712], [-674], [-628], [-602], [-610], [-600], [-544], [-510], [-522], [-533], [-527], [-519], [-518], [-513], [-490], [-492], [-508], [-488], [-470], [-491], [-542], [-587], [-613], [-628], [-635], [-644], [-659], [-669], [-660], [-638], [-644], [-667], [-665], [-635], [-612], [-599], [-574], [-543], [-526], [-516], [-487], [-449], [-430], [-421], [-409], [-413], [-414], [-435], [-470], [-495], [-540], [-559], [-560], [-544], [-541], [-543], [-508], [-476], [-467], [-472], [-455], [-436], [-405], [-365], [-327], [-301], [-295], [-274], [-246], [-221], [-215], [-210], [-193], [-194], [-215], [-240], [-263], [-297], [-318], [-308], [-304], [-325], [-336], [-324], [-309], [-304], [-302], [-302], [-287], [-263], [-239], [-218], [-224], [-230], [-209], [-186], [-171], [-157], [-133], [-109], [-101], [-80], [-61], [-80], [-115], [-128], [-121], [-132], [-165], [-192]]
        outdata[:] = [[0] for i in range(sd.default.blocksize)]
        if now() - client_last_frame_timestamp > 2:
            print("长时间闲置，SOUNDWIRE 输出正在关闭。。。")
            global soundwire_client_switch
            soundwire_client_switch = False


def soundwire_client():
    global soundwire_client_switch
    with sd.OutputStream(callback=callback_client):
        print('SOUND WIRE CLIENT IS RUNNING')
        ui.show_toast("SOUNDWIRE 正在接收音频广播")
        eel.set_receiving_pcm_state(True)
        while True:
            if not soundwire_client_switch:
                break
            sd.sleep(100)
        print('SOUND WIRE CLIENT DOWN')
        ui.show_toast("SOUNDWIRE 音频接收端已休眠")
        eel.set_receiving_pcm_state(False)


def is_soundwire_host_running():
    global soundwire_host_switch
    return soundwire_host_switch


def start_soundwire_host():
    global soundwire_host_switch
    if is_soundwire_host_running():
        return
    soundwire_host_switch = True
    threading.Thread(target=soundwire_host).start()
    threading.Thread(target=broadcast_start_flag).start()
    ui.set_soundwire_host_switch(True)
    eel.update_soundwire_switch()


def stop_soundwire_host():
    global soundwire_host_switch
    soundwire_host_switch = False
    ui.set_soundwire_host_switch(False)
    eel.update_soundwire_switch()


def is_soundwire_client_running():
    global soundwire_client_switch
    return soundwire_client_switch


def start_soundwire_client():
    global soundwire_client_switch
    if is_soundwire_client_running():
        return
    soundwire_client_switch = True
    threading.Thread(target=soundwire_client).start()


def stop_soundwire_client():
    global soundwire_client_switch
    soundwire_client_switch = False


def handle_conflict(remote_targets):
    for ip in settings.soundwire_target:
        if ip in remote_targets:
            settings.pop_soundwire_target(ip)
            eel.update_soundwire_target()
            ui.show_error("广播冲突", "网络内存在多个音频广播,到{}的广播已被停止".format(ip))
