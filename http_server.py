from flask import Flask,render_template,request
import threading,time



app = Flask("LanBridge HTTP Server",
            static_url_path='/assets',
            template_folder='ui/templates',
            static_folder='ui/assets')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 36000
import plugins.file_explorer
import http_api


def runflask():
    app.run(
                 host='0.0.0.0',
                 port= 8000,
                 debug=False,
                 threaded=True
                 )

def start():
    threading.Thread(target=runflask).start()
