import time,asyncio,threading,requests,json
from websockets import WebSocketException
from ui import ui
from db.api import add_conn_log
import eel

class clients_lan:
    def __init__(self):
        self.data={}
        self.blocked_list=["0.0.0.0","127.0.0.1"]
    def is_ws_connected(self,ip):
        return (ip in self.data and self.data[ip]["send_queue"]!=None and self.data[ip]["ws_connected"])
    def get(self,ip):
        return self.data[ip] if ip in self.data else None
    def add(self,ip):
        if ip in self.data or ip in self.blocked_list:
            return
        self.data[ip]={
                "birth_time" : round(time.time() * 1000),
                "send_queue" : None,
                "ws_connected" : False,
                "battery" : {"has_battery":False},
                "sys_info" : {}
            }
        add_conn_log(ip,hostname='',mac='',platform='')
    def init_info(self,ip):
        from plugins.battery import get_remote_battery_status
        battery_status = get_remote_battery_status(ip)
        self.set_battery_status(ip,battery_status)
        self.set_sys_info(ip)

    def set_sys_info(self,ip):
        try:
            result = requests.get("http://{}:{}/api/sys_info".format(ip,8000))
            data = json.loads(result.text)
            self.data[ip]["sys_info"] = data
        except Exception as e:
            print("get_remote_sys_info failed",e)
        
    def set_battery_status(self,ip,data):
        self.data[ip]["battery"] = data
        eel.update_all_lan_clients()
        
    def get_battery_status(self,ip):
        return self.data[ip]["battery"]
    
    def set_ws_connected(self,ip,msg_queue,conn):
        if ip not in self.data:
            return
        self.data[ip]["send_queue"] = msg_queue
        self.data[ip]["ws_conn"] = conn
        self.data[ip]["ws_connected"] = True
        print(self.data)
        ui.show_toast("与{}建立连接".format(ip))
        """下面开始连接建立后的事件"""
        from plugins.sync_folder import resync as sync_folder_resync
        sync_folder_resync(ip)
        self.init_info(ip)
        eel.update_all_lan_clients()
        ui.set_client_num(self.available_send_queue_count())
    def set_ws_disconnected(self,ip):
        if ip not in self.data:
            return
        if not self.data[ip]["ws_connected"]:
            return
        self.data[ip]["send_queue"]=None
        self.data[ip]["ws_connected"]=False
        print(self.data)
        ui.show_toast("与{}连接断开".format(ip))
        """下面开始连接断开后的事件"""
        eel.update_all_lan_clients()
        ui.set_client_num(self.available_send_queue_count())
    def all_available_send_queue(self):
        result={}
        for ip in self.data:
            if self.data[ip]["ws_connected"]:
                result[ip]=self.data[ip]
        return result
    def available_send_queue_count(self):
        return len(self.all_available_send_queue())
    def send(self,queue,msg):
        if queue.full():
            queue.get_nowait()
            print("bad connection")
        queue.put_nowait(msg)
    def send_to(self,ip,msg):
        if not ip in self.data or not self.data[ip]["ws_connected"]:
            return
        try:
                queue = self.data[ip]["send_queue"]
                self.send(queue,msg)
        except WebSocketException as e:
                print("websocket client exception:",e,ip)
                print(ip,"LOSE CONNETION")
                self.set_ws_disconnected(ip)
    def broadcast(self,msg,target_ips=None):
        if target_ips is not None:
            clients = {}
            for ip in target_ips:
                if self.is_ws_connected(ip):
                    clients[ip] = self.get(ip)
        else:
            clients = self.all_available_send_queue()
            
        for ip in clients:
            try:
                queue = clients[ip]["send_queue"]
                self.send(queue,msg)
                #print(msg,"->",ip)
            except WebSocketException as e:
                print("websocket client exception:",e,ip)
                print(ip,"LOSE CONNETION")
                self.set_ws_disconnected(ip)
                
clients_lan = clients_lan()
