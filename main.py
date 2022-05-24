import socket
import sys
import time


def ApplicationInstance():
    try:
        global s
        s = socket.socket()
        host = socket.gethostname()
        s.bind((host, 60123))
    except:
        print("instance is running... exit after 5 secs")
        time.sleep(5)
        sys.exit(0)


if __name__ == "__main__":
    ApplicationInstance()

    import ws_server
    ws_server.start()
    import http_server
    http_server.start()
    import plugins.battery as battery
    battery.start_battery_deamon()
    import plugins.sync_folder as sync_folder
    sync_folder.start_sync_folder_observer()
    from ui import app
    import sniff
    sniff.start()
    sys.exit(app.exec())
