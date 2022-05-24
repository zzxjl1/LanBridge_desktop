from PyQt6.QtWidgets import QMainWindow,QSystemTrayIcon,QMenu,QMessageBox,QFileDialog,QApplication,QLabel,QProgressBar
from PyQt6.QtCore import QUrl,pyqtSignal,pyqtSlot,QPoint,QSettings,Qt,QTimer
from PyQt6.QtGui import QIcon,QAction,QActionGroup
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings

import threading,os,sys,time
from toolutils import getpath,is_win,is_mac
from settings import settings as plugin_settings
settings = QSettings("Wu_Eden","Lan_Bridge")


#os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = "5588"
#QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True) #enable highdpi scaling
#QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True) #use highdpi icons

import eel
eel.init(os.path.join(getpath(),"ui"),allowed_extensions=[".html"])
import js_bridge
def start_eel():
    eel.start('index.html',port=8080,block=True,mode=None)#close_callback=ui.webview_close_callback
threading.Thread(target=start_eel).start()


class TrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        super(TrayIcon, self).__init__(parent)
        self.showMenu()

    def showMenu(self):

        self.menu = QMenu()
        self.settings_menu = QMenu()
        
        self.show_webview = QAction("打开管理页面", self, triggered=self.parent().show_webview)
        
        self.client_num = QAction("当前带机数：0", self)
        self.client_num.setEnabled(False)

        self.clipboard_share_switch = QAction("剪切板同步", self,triggered=self.toggle_clipboard_share)
        self.clipboard_share_switch.setCheckable(True)
        
        self.soundwire_host_switch = QAction("从我串流音频", self,triggered=self.toggle_soundwire_host)
        self.soundwire_host_switch.setCheckable(True)
        
        self.settings_menu_avoid_disturb = QAction("勿扰模式", self,triggered=self.parent().toggle_undisturb_mode)
        self.settings_menu_avoid_disturb.setCheckable(True)
        
        self.quitAction = QAction("退出", self, triggered=self.quit)

        self.menu.addAction(self.show_webview)
        self.menu.addAction(self.client_num)
        self.menu.addAction(self.clipboard_share_switch)  
        self.menu.addAction(self.soundwire_host_switch)  
        self.settings_menu.addAction(self.settings_menu_avoid_disturb)
        self.settings_menu.setTitle("设置")
        self.menu.addMenu(self.settings_menu,)
        self.menu.addAction(self.quitAction)

        #把鼠标点击图标的信号和槽连接
        self.activated.connect(self.iconClied)
        #把鼠标点击弹出消息的信号和槽连接
        self.messageClicked.connect(self.msg_clicked)
        self.icon = QIcon(getpath()+"/icon.png")
        self.setIcon(self.icon)
        self.setContextMenu(self.menu)
        self.setToolTip("LanBridge")
        
    def toggle_clipboard_share(self,checked):
        from plugins.clipboard import clipboard_share_start,clipboard_share_stop
        if checked:
            clipboard_share_start()
        else:
            clipboard_share_stop()

    def toggle_soundwire_host(self,checked):
        from plugins.soundwire import start_soundwire_host,stop_soundwire_host
        if checked:
            start_soundwire_host()
        else:
            stop_soundwire_host()
            
    @pyqtSlot(bool) 
    def set_undisturb_switch(self,state):
        self.settings_menu_avoid_disturb.setChecked(state)   
    @pyqtSlot(bool)        
    def set_clipboard_share_switch(self,state):
        self.clipboard_share_switch.setChecked(state)        
    @pyqtSlot(bool)        
    def set_soundwire_host_switch(self,state):
        self.soundwire_host_switch.setChecked(state)
    @pyqtSlot(str,str)   
    def show_toast(self,title='',body=''):
        self.menu.hide()
        self.showMessage(title,body,self.icon,1000)
    @pyqtSlot(str,str) 
    def show_error(self,title='',body=''):
        QMessageBox.critical(self.parent(),title,body,QMessageBox.StandardButton.Ok)
    @pyqtSlot(str)
    def set_client_num(self,s):
        self.client_num.setText("当前带机数："+s)
    def iconClied(self, reason):
        print(reason)
        "鼠标点击icon传递的信号会带有一个整形的值，1是表示单击右键，2是双击，3是单击左键，4是用鼠标中键点击"
        if reason == QSystemTrayIcon.ActivationReason.Trigger or reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.parent().show_webview()
        
    def msg_clicked(self):
        pass
        #self.showMessage("提示", "你点了消息",self.icon,2000)
        #self.open()
    
    def show_msg(self):
        self.showMessage("测试", "我是消息",0,2000)
          
    def quit(self):
        self.hide()
        import os
        os._exit(0)



class webview(QMainWindow):
    def __init__(self, parent=None):
        super(QMainWindow, self).__init__()
        # 设置窗口标题
        self.setWindowTitle('LanBridge')
        self.setWindowFlags(Qt.WindowType.Window|Qt.WindowType.WindowTitleHint|Qt.WindowType.WindowCloseButtonHint|Qt.WindowType.WindowMinimizeButtonHint)
        # 设置窗口图标
        self.setWindowIcon(QIcon(getpath()+'/icon.png'))
        # 设置窗口大小
        self.resize(1000, 600)
        # 设置浏览器
        self.browser = QWebEngineView()
        url = "http://localhost:8080"
        # 指定打开界面的 URL
        self.browser.setUrl(QUrl(url))
        self.browser.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.browser.settings().setFontFamily(QWebEngineSettings.FontFamily.StandardFont,"Microsoft YaHei")
        # 添加浏览器到窗口中
        self.setCentralWidget(self.browser)
    def closeEvent(self, event):
        ui.webview_shown=False
        self.hide()
        print("webview closed")

class drag_file_dialog(QMainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()
        self.setWindowTitle('LanBridge文件发送')
        self.setWindowIcon(QIcon(getpath()+'/icon.png'))
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint|Qt.WindowType.WindowCloseButtonHint)
        self.setFixedSize(500, 200)
        self.QLabel = QLabel(self)
        self.QLabel.setText("请将要发送的文件拖入这里")
        self.setStyleSheet("""QLabel{font-size:30px;font-family: "PingFang SC", "Heiti SC", "Microsoft YaHei", "WenQuanYi Micro Hei";}""")
        self.QLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblHidden = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.flashLbl)
        
        self.setAcceptDrops(True)
        self.setCentralWidget(self.QLabel)

    @pyqtSlot(str)
    def show_dialog(self,t):
        self.setWindowTitle("LanBridge文件发送 to：{}".format(t))
        self.timer.start(500)
        self.show()
        
    def flashLbl(self):
        if self.lblHidden:
            self.QLabel.show()
            self.lblHidden = False
        else:
            self.QLabel.hide()
            self.lblHidden = True
            
    # 鼠标拖入事件
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
 
    # 鼠标放开执行
    def dropEvent(self, event):
        files = [i.toLocalFile() for i in event.mimeData().urls()]
        print(files)
        from plugins.file_transmit import set_path
        set_path(files)
        self.timer.stop()
        self.close()

class file_transfer_progress_dialog(QMainWindow):
    def __init__(self, parent= None):
        super(QMainWindow, self).__init__()

        self.sending_label_str = "正在发送："
        self.count_label_str = "第x个，共x个"
        self.file_progress_num = 0
        self.total_progress_num = 0
    
        self.setFixedSize(700,120)
        self.setWindowTitle('文件传输进度')
        self.setWindowIcon(QIcon(getpath()+'/icon.png'))
        self.setWindowFlags(Qt.WindowType.WindowMinimizeButtonHint|Qt.WindowType.WindowStaysOnTopHint)
        self.file_progress = QProgressBar(self)
        self.file_progress.setTextVisible(False)
        self.file_progress.setGeometry(30, 20, 640, 30)
        self.sending_label = QLabel(self)
        self.sending_label.setText(self.sending_label_str)
        self.sending_label.setGeometry(30, 20, 640, 30)
        self.sending_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.total_progress = QProgressBar(self)
        self.total_progress.setTextVisible(False)
        self.total_progress.setGeometry(30, 70, 640, 30)
        self.count_label = QLabel(self)
        self.count_label.setText(self.count_label_str)
        self.count_label.setGeometry(30, 70, 640, 30)
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        
    @pyqtSlot(str)
    def show_dialog(self,t):
        self.timer.start(200)
        self.setWindowTitle("文件传输进度 to：{}".format(t))
        self.show()
    @pyqtSlot(str)
    def set_sending_label(self,t):
        self.sending_label_str = "正在发送：{}".format(t)
    @pyqtSlot(str)
    def set_count_label(self,t):
        self.count_label_str = t
    @pyqtSlot(int)
    def set_file_progress(self,t):
        self.file_progress_num = t
    @pyqtSlot(int)
    def set_total_progress(self,t):
        self.total_progress_num = t
    @pyqtSlot(str)
    def complete(self,t):
        self.timer.stop()
        self.close()
        
    def update(self):
        self.count_label.setText(self.count_label_str)
        self.sending_label.setText(self.sending_label_str)
        self.file_progress.setValue(self.file_progress_num)
        self.total_progress.setValue(self.total_progress_num)
        
class find_my_device_dialog(QMainWindow):
    def __init__(self, parent=None):
        super(QMainWindow, self).__init__()
        self.setWindowTitle('查找设备')
        self.setWindowIcon(QIcon(getpath()+'/icon.png'))
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint|Qt.WindowType.WindowCloseButtonHint)
        self.browser = QWebEngineView()
        self.browser.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.browser.settings().setFontFamily(QWebEngineSettings.FontFamily.StandardFont,"Microsoft YaHei")
        self.browser.settings().setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        self.browser.page().windowCloseRequested.connect(self.close_dialog)
        self.setCentralWidget(self.browser)
        
    @pyqtSlot(str)
    def show_dialog(self,t):
        url = "http://localhost:8080/find_my_device.html"
        self.browser.setUrl(QUrl(url))
        if is_mac():
            self.showMaximized()
        else:
            self.showFullScreen()
    def close_dialog(self):
        self.close()
        
class ui(QMainWindow):
    def __init__(self, parent=None):
        self.webview_shown = False
        self.last_toast_data = {"title":"","body":""}
        self.last_toast_timestamp = time.time()
        super(QMainWindow, self).__init__(parent)
        self.tray_icon = TrayIcon(self)
        self.tray_icon.show()
        self.webview = webview(self)
        self.show_webview()
        self.drag_file_dialog = drag_file_dialog()
        self.file_transfer_progress_dialog = file_transfer_progress_dialog()
        self.find_my_device_dialog = find_my_device_dialog()
        
    def show_webview(self):
        if self.webview_shown:
            self.webview.activateWindow()
            self.webview.raise_()
            return
        self.webview_shown=True
        self.webview.show()
        self.webview.activateWindow()  
        self.webview.raise_()
        print("webview opened")
        
    def is_undisturb_mode_on(self):
        return plugin_settings.undisturb_mode_switch
    def toggle_undisturb_mode(self,t):
        import eel
        plugin_settings.set_undisturb_switch(t)
        eel.update_undisturb_mode_switch()
        self.set_undisturb_switch(t)
        
    set_client_num_signal=pyqtSignal(str)
    show_toast_signal=pyqtSignal(str,str)
    show_error_signal=pyqtSignal(str,str)
    set_clipboard_share_switch_signal=pyqtSignal(bool)
    set_soundwire_host_switch_signal=pyqtSignal(bool)
    set_undisturb_switch_signal=pyqtSignal(bool)
    show_drag_file_signal=pyqtSignal(str)
    show_file_transfer_progress_signal=pyqtSignal(str)
    set_file_transfer_progress_sending_label_signal=pyqtSignal(str)
    set_file_transfer_progress_count_label_signal=pyqtSignal(str)
    set_file_transfer_progress_file_progress_signal=pyqtSignal(int)
    set_file_transfer_progress_total_progress_signal=pyqtSignal(int)
    complete_file_transfer_progress_signal=pyqtSignal(str)
    show_find_my_device_dialog_signal=pyqtSignal(str)
    def set_client_num(self,s):
        self.set_client_num_signal.connect(self.tray_icon.set_client_num)
        self.set_client_num_signal.emit(str(s))
    def show_toast(self,title='',body=''):
        if plugin_settings.undisturb_mode_switch:
            return
        if time.time() - self.last_toast_timestamp < 2 and self.last_toast_data == {"title":title,"body":body}:
            return
        self.last_toast_data = {"title":title,"body":body}
        self.last_toast_timestamp = time.time()
        self.show_toast_signal.connect(self.tray_icon.show_toast)
        self.show_toast_signal.emit(title,body)
    def show_error(self,title,body):
        self.show_error_signal.connect(self.tray_icon.show_error)
        self.show_error_signal.emit(title,body)
    def set_clipboard_share_switch(self,state):
        self.set_clipboard_share_switch_signal.connect(self.tray_icon.set_clipboard_share_switch)
        self.set_clipboard_share_switch_signal.emit(state)
    def set_soundwire_host_switch(self,state):
        self.set_soundwire_host_switch_signal.connect(self.tray_icon.set_soundwire_host_switch)
        self.set_soundwire_host_switch_signal.emit(state)
    def show_drag_file_dialog(self,ip):
        self.show_drag_file_signal.connect(self.drag_file_dialog.show_dialog)
        self.show_drag_file_signal.emit(ip)
    def set_undisturb_switch(self,state):
        self.set_undisturb_switch_signal.connect(self.tray_icon.set_undisturb_switch)
        self.set_undisturb_switch_signal.emit(state)
        
    def show_file_transfer_progress_dialog(self,ip):
        self.show_file_transfer_progress_signal.connect(self.file_transfer_progress_dialog.show_dialog)
        self.show_file_transfer_progress_signal.emit(ip)
    def set_file_transfer_progress_sending_label(self,t):
        self.set_file_transfer_progress_sending_label_signal.connect(self.file_transfer_progress_dialog.set_sending_label)
        self.set_file_transfer_progress_sending_label_signal.emit(t)
    def set_file_transfer_progress_count_label(self,t):
        self.set_file_transfer_progress_count_label_signal.connect(self.file_transfer_progress_dialog.set_count_label)
        self.set_file_transfer_progress_count_label_signal.emit(t)
    def set_file_transfer_progress_file_progress(self,t):
        self.set_file_transfer_progress_file_progress_signal.connect(self.file_transfer_progress_dialog.set_file_progress)
        self.set_file_transfer_progress_file_progress_signal.emit(int(t))
    def set_file_transfer_progress_total_progress(self,t):
        self.set_file_transfer_progress_total_progress_signal.connect(self.file_transfer_progress_dialog.set_total_progress)
        self.set_file_transfer_progress_total_progress_signal.emit(int(t))
    def complete_file_transfer_progress(self):
        self.complete_file_transfer_progress_signal.connect(self.file_transfer_progress_dialog.complete)
        self.complete_file_transfer_progress_signal.emit('')
    def show_find_my_device_dialog(self):
        self.show_find_my_device_dialog_signal.connect(self.find_my_device_dialog.show_dialog)
        self.show_find_my_device_dialog_signal.emit('')
    
if is_win():
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u'com.zzxjl1.lanbridge')

app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)
ui=ui()




