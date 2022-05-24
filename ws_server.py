import threading,time,json
from connections import clients_lan
import asyncio,queue
from websockets import serve,WebSocketException
from ws_handler import ws_handler,consumer_handler,producer_handler

    
async def echo(websocket):
    ip=websocket.remote_address[0]
    print("websocket server 收到传入连接！",ip)
    clients_lan.add(ip)
    if clients_lan.is_ws_connected(ip):
        print("duplicate ws conn,aborting old!")
        #await clients_lan.data[ip]["ws_conn"].close()
    msg_queue = queue.Queue(maxsize=5)
    clients_lan.set_ws_connected(ip,msg_queue,websocket)
    loop = asyncio.get_event_loop()
    try:
        await asyncio.gather(
            consumer_handler(loop,websocket,ip),
            producer_handler(loop,websocket,msg_queue),
        )
    except Exception as e:
        print("websocket server exception:",e,ip)
        import traceback
        print(traceback.format_exc())
        print(ip,"LOSE CONNETION")
        clients_lan.set_ws_disconnected(ip)

async def main():
    async with serve(echo, "0.0.0.0", 8765):
        await asyncio.Future()  # run forever
        
def run_ws_server():
    asyncio.run(main())
    
def start():
    threading.Thread(target=run_ws_server).start()
