from db.db_utils import db
import datetime

def get_plugin_switch(name):
    result = db.query("select switch from plugin_switch where name=?;",(name,))
    if not result:
        return False
    return result[0][0]

def set_plugin_switch(name,status):
    db.execute("update plugin_switch set switch=? where name=?;",(status,name))

def get_hostname_alias(mac_addr):
    if not mac_addr:
        return
    result = db.query("select alias from hostname_alias where mac=?;",(mac_addr,))
    if not result:
        return
    return result[0][0]

def set_hostname_alias(mac_addr,alias):
    if not mac_addr:
        return
    if not alias:
        del_hostname_alias(mac_addr)
        return
    if get_hostname_alias(mac_addr):
        db.execute("update hostname_alias set alias=? where mac=?;",(alias,mac_addr))
    else:
        db.execute("insert into hostname_alias(mac,alias) values(?,?);",(mac_addr,alias))
        
def del_hostname_alias(mac_addr):
    db.execute("delete from hostname_alias where mac=?;",(mac_addr,))

def add_conn_log(ip='',hostname='',mac='',platform=''):
    db.execute("insert into conn_log(ip,hostname,mac,platform,time_stamp) values(?,?,?,?,?);",
               (ip,hostname,mac,platform,datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
