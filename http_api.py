from flask import Flask,render_template,request,Blueprint,jsonify,send_file,abort
from http_server import app
import os
from toolutils import get_sys_info,getpath,normalize_path,show_folder
from plugins.sync_folder import get_sync_folder_structure
import plugins.power_management as power
from plugins.battery import battery_data

api=Blueprint('api',__name__)

@api.route('/sys_info')
def sys_info():
    return jsonify(get_sys_info())
@api.route('/battery_status')
def battery_status():
    return jsonify(battery_data())
@api.route('/sync_folder_structure')
def sync_folder_structure():
    return jsonify(get_sync_folder_structure())
@api.route('/sync_file_download')
def sync_file_download():
    path = request.args.get("path")
    if not os.path.isfile(path):
        abort(404)
    print("received sync_file_download:",path)
    return send_file(path)

@api.route('/find_my_device')
def find_my_device():
    from ui import ui
    ui.show_find_my_device_dialog()
    return ('', 204)

@api.route('/shutdown')
def shutdown():
    power.shutdown()
    import os
    os._exit(0)
    return ('', 204)
@api.route('/restart')
def restart():
    power.restart()
    import os
    os._exit(0)
    return ('', 204)
@api.route('/hibernate')
def hibernate():
    power.hibernate()
    return ('', 204)

@api.route('/debug')
def debug():
    from connections import clients_lan
    print(clients_lan.data)
    return "见console"

@api.route('/file_transmit', methods=['POST'])
def file_transmit():
    ptype = request.form.get('type')
    root = request.form.get('root')
    tag = request.form.get('tag')
    if ptype == "file":
        f = request.files['file']
        path = os.path.join(getpath(),"files_received",tag,root,f.filename)
        os.makedirs(os.path.dirname(path),exist_ok=True)
        f.save(path)
    elif ptype == "dir":
        os.makedirs(os.path.join(getpath(),"files_received",tag,root),exist_ok=True)
    return ('', 204)

@api.route('/show_transmit_folder')
def show_transmit_folder():
    from ui import ui
    tag = request.args.get('tag')
    ui.show_toast("文件传输完成：{}".format(tag))
    show_folder(os.path.join("files_received",tag))
    return ('', 204)

app.register_blueprint(api,url_prefix='/api')
app.config['JSON_AS_ASCII'] = False
