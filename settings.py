from db.api import get_plugin_switch,set_plugin_switch

class settings():
    def __init__(self):
        self.undisturb_mode_switch = get_plugin_switch("undisturb_mode")
        self.clipboard_share_switch = get_plugin_switch("clipboard_share")
        self.soundwire_target = []

    def set_undisturb_switch(self,t):
        self.undisturb_mode_switch = t
        set_plugin_switch("undisturb_mode",t)

    def set_clipboard_share_switch(self,t):
        self.clipboard_share_switch = t
        set_plugin_switch("clipboard_share",t)

    def set_soundwire_target(self,t):
        self.soundwire_target = t

    def pop_soundwire_target(self,t):
        if t in self.soundwire_target:
            self.soundwire_target.remove(t)
        
settings = settings()
