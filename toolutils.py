import os,sys,platform,hashlib,socket,threading,requests,json,subprocess
from getmac import get_mac_address
def get_ip():
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    s.connect(('8.8.8.8',80))
    ip=s.getsockname()[0]
    s.close()
    return ip

def normalize_path(path):
    return path.replace("\\","/")

def getpath():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

def get_sys_info():
    return {"platform":platform.platform(aliased=True,terse=True),
            "hostname":platform.node(),
            "architecture":platform.machine(),
            "processor":platform.processor(),
            "system":platform.system(),
            "mac":get_mac_address()
            }

def md5(path):
    f = open(getpath()+path,'rb')
    md5_obj = hashlib.md5()
    md5_obj.update(f.read())
    hash_code = md5_obj.hexdigest()
    f.close()
    return str(hash_code).lower()

def is_win():
    return platform.system()=='Windows'
def is_mac():
    return platform.system()=='Darwin'

def safe_serialize(obj):
  default = lambda o: f"<<non-serializable: {type(o).__qualname__}>>"
  return json.dumps(obj, default=default)

def show_folder(relpath):
    from toolutils import getpath
    path = os.path.join(getpath(),relpath)
    if sys.platform == "win32":
        os.startfile(path)
    else:
        opener ="open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, path])

def debounce(wait_time):
    def decorator(function):
        def debounced(*args, **kwargs):
            def call_function():
                debounced._timer = None
                return function(*args, **kwargs)

            if debounced._timer is not None:
                debounced._timer.cancel()

            debounced._timer = threading.Timer(wait_time, call_function)
            debounced._timer.start()

        debounced._timer = None
        return debounced
    return decorator

