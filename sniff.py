import time,json,uuid
import threading
import socket
from retrying import retry   
from getmac import get_mac_address
from connections import clients_lan
import asyncio,queue
from websockets import connect,WebSocketException
from ws_handler import ws_handler,consumer_handler,producer_handler

interval = 2
port = 65535
uuid_str = str(uuid.uuid1())

def get_ip():
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    s.connect(('8.8.8.8',80))
    ip=s.getsockname()[0]
    s.close()
    return ip

def on_exception(exception):
    print("网络发现error",exception)
    return True


@retry(wait_fixed=1000,retry_on_exception = on_exception)
def 网络发现广播receiver():
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    client.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client.bind(("", port))
    while True:
        data, (remote_ip,remote_port) = client.recvfrom(1024)
        #print("网络发现广播receiver received message: %s"%data)
        sniff_broadcast_data=json.loads(str(data, encoding = "utf8"))
        if sniff_broadcast_data["uuid"] == uuid_str:
            continue
        clients_lan.add(remote_ip)
        if clients_lan.is_ws_connected(remote_ip):
            continue    
        async def wsclient(remote_ip):
            try:
                async with connect("ws://{}:8765".format(remote_ip)) as websocket:
                    print("websocket client 连接建立！ to:",remote_ip)
                    msg_queue = queue.Queue(maxsize=5)
                    clients_lan.set_ws_connected(remote_ip,msg_queue,websocket)
                    loop = asyncio.get_event_loop()
                    await asyncio.gather(
                        consumer_handler(loop,websocket,remote_ip),
                        producer_handler(loop,websocket,msg_queue))
            except Exception as e:
                print("websocket client exception:",e,remote_ip)
                #import traceback
                #print(traceback.format_exc())
                print(remote_ip,"LOSE CONNETION")
                clients_lan.set_ws_disconnected(remote_ip)
        def main():
            asyncio.run(wsclient(remote_ip))
        threading.Thread(target=main).start()
        

@retry(wait_fixed=1000,retry_on_exception = on_exception)
def 网络发现广播sender():
    sniffer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sniffer.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    sniffer.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sniffer.settimeout(interval)
    while True:
        ip_address = get_ip()
        mac_address = get_mac_address(ip=ip_address)
        message = json.dumps({"ip":ip_address,
                            "timestamp":round(time.time() * 1000),
                            "mac":mac_address,
                            "udp_broadcast_interval_in_ms":interval*1000,
                            "uuid":uuid_str
                            })
        sniffer.sendto(bytes(message, encoding = "utf8") , ('<broadcast>', port))
        #print("网络发现广播sender: message sent!")
        time.sleep(interval)    

def start():
    threading.Thread(target=网络发现广播sender).start()
    threading.Thread(target=网络发现广播receiver).start()
