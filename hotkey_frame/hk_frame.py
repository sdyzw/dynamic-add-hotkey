import ctypes
import json
import logging
import os
import sys
from collections import defaultdict
from ctypes import GetLastError
from ctypes import c_bool, c_int, WINFUNCTYPE
from ctypes.wintypes import UINT

import pyWinhook
import pythoncom
from PyQt5.Qt import *
from PyQt5.QtCore import QAbstractNativeEventFilter

from hotkey_frame import TM

base_dir = os.path.dirname(__file__)
sys.path.append(base_dir)
PEN_SVG = '<svg t="1614852452011" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="2593" width="200" height="200"><path d="M1000.106667 100.336124l-76.76031-76.60155c-31.831318-31.672558-83.348837-31.672558-115.180155 0l-96.049612 95.732093 192.019845 191.464186 95.970233-95.652713C1031.937984 183.526202 1031.937984 132.088062 1000.106667 100.336124zM154.235039 675.60186l192.019845 191.464186 522.00186-516.365891L676.236899 159.235969 154.235039 675.60186zM0 1024l307.2-121.213023L116.847132 712.910388 0 1024z" p-id="2594"></path></svg>'

SAVE_SVG = '<svg t="1614924554890" class="icon" viewBox="0 0 1027 1024" version="1.1" ' \
           'xmlns="http://www.w3.org/2000/svg" p-id="2662" width="200" height="200"><path d="M963.086652 225.820142 ' \
           '62.417562 225.820142c-34.472116 0-62.417585 27.945469-62.417585 62.417585l0 436.632475c0 34.474163 ' \
           '27.945469 62.417585 62.417585 62.417585L963.086652 787.287787c34.473139 0 62.415538-27.944446 ' \
           '62.415538-62.417585L1025.50219 288.237727C1025.50219 253.764588 997.557745 225.820142 963.086652 ' \
           '225.820142zM164.891444 492.5316c-4.906753-0.209778-9.274224-2.0241-13.111622-5.436826-3.837398-3.837398-5' \
           '.756097-8.099469-5.756097-12.791327 0.209778-5.116531 2.343371-9.91379 6.395664-14.390755 ' \
           '27.28646-30.908964 45.833885-65.556065 55.642275-103.930047 1.918699-6.180769 5.116531-10.338463 ' \
           '9.593496-12.472056 4.047176-2.343371 8.739035-2.87856 14.07046-1.599428 4.686742 1.708921 8.314363 ' \
           '4.586458 10.872628 8.634658 4.476965 10.447956-2.667759 34.326806-21.425985 71.631434 0.209778 0.214894 ' \
           '0.320295 0.429789 0.320295 0.639566l0 203.382107c-0.214894 5.965875-2.028193 10.872628-5.436826 ' \
           '14.710027-3.412726 3.40761-7.78429 5.221932-13.111622 ' \
           '5.436826-5.331425-0.214894-9.702989-1.918699-13.111622-5.116531-3.412726-4.052293-5.116531-9.063423-5' \
           '.116531-15.030321L184.715955 478.780411C176.828311 487.73434 170.217753 492.321822 164.891444 ' \
           '492.5316zM363.476292 627.480104c-0.214894 5.965875-2.028193 10.872628-5.436826 14.710027-3.412726 ' \
           '3.40761-7.78429 5.221932-13.111622 ' \
           '5.436826-5.331425-0.214894-9.702989-1.918699-13.111622-5.116531-3.412726-4.052293-5.116531-9.063423-5' \
           '.116531-15.030321l0-76.428693c-8.314363 10.447956-16.309454 19.61678-23.984251 27.501354-28.995381 ' \
           '28.350698-49.036833 41.571814-60.119239 ' \
           '39.653115-4.691859-1.708921-8.423857-4.586458-11.192923-8.634658-2.558265-5.116531-3.197832-9.702989-1' \
           '.918699-13.751189 1.279133-5.116531 4.582365-9.274224 9.91379-12.472056 27.926026-18.332531 ' \
           '50.310849-39.653115 67.154469-63.956637l-55.002708 0c-5.756097 ' \
           '0-10.233062-1.703805-13.430894-5.116531-3.412726-3.622504-5.116531-8.099469-5.116531-13.430894 0-5.326309 ' \
           '1.703805-9.698896 5.116531-13.111622 3.197832-3.40761 7.674796-5.116531 13.430894-5.116531l75.149561 0 ' \
           '0-15.030321-49.566906 0c-7.465019-0.209778-13.221116-2.982938-17.268292-8.314363-5.116531-6.605442-7' \
           '.569396-13.536294-7.355525-20.786419l0-60.758806c0-6.605442 2.343371-12.472056 7.03523-17.588587 ' \
           '5.116531-4.901637 10.978029-7.355525 17.588587-7.355525l18.86772 0 112.563682 0c8.524141-0.209778 ' \
           '15.669888 2.348488 21.425985 7.674796 4.901637 4.476965 7.459902 10.233062 7.674796 17.268292l0 ' \
           '60.758806c-0.214894 7.674796-3.307326 14.500249-9.274224 20.466124-5.970992 5.756097-12.58155 ' \
           '8.634658-19.826558 8.634658l-45.089941 0 0 15.030321 76.108399 0c5.541203 0 9.91379 1.599428 13.111622 ' \
           '4.797259 3.40761 3.62762 5.116531 8.104585 5.116531 13.430894 0 5.331425-1.708921 9.702989-5.116531 ' \
           '13.111622-3.412726 3.62762-7.78429 5.436826-13.111622 5.436826l-57.560974 0c16.838503 23.87885 39.97341 ' \
           '45.409213 69.393463 64.596204 5.326309 3.62762 8.419763 7.995091 9.274224 13.111622 0.424672 ' \
           '5.116531-0.74906 9.698896-3.518127 13.751189-3.412726 4.26207-7.355525 6.715959-11.83249 ' \
           '7.355525-5.116531 0.849344-10.233062-0.429789-15.349593-3.837398-25.797549-17.907858-47.967478-38.373982' \
           '-66.514903-61.398372L363.474245 627.480104zM398.972737 ' \
           '390.520251c-1.708921-1.488911-3.307326-2.238994-4.797259-2.238994l-98.17395 0c-1.918699 0-3.518127 ' \
           '0.639566-4.797259 1.918699-1.494027 1.494027-2.133593 3.197832-1.918699 5.116531l0 30.05962c0 1.494027 ' \
           '0.639566 2.988054 1.918699 4.476965 1.279133 1.494027 2.87856 2.238994 4.797259 2.238994l98.17395 ' \
           '0c1.918699 0 3.518127-0.744967 4.797259-2.238994 1.064238-1.488911 1.703805-2.982938 ' \
           '1.918699-4.476965l0-30.05962C400.891436 393.613706 400.25187 392.014278 398.972737 390.520251zM608.750508 ' \
           '524.509918c-4.692882 3.412726-9.702989 5.01113-15.030321 ' \
           '4.797259-4.053316-0.639566-7.995091-3.197832-11.83249-7.674796-3.413749-4.686742-5.012154-9.378601-4' \
           '.797259-14.07046 0.849344-5.756097 7.779174-13.536294 20.786419-23.344684 26.222221-22.169929 ' \
           '48.927339-49.246611 68.11433-81.224929l-62.677505 0c-5.756097 ' \
           '0-10.233062-1.703805-13.430894-5.116531-3.413749-3.622504-5.116531-8.099469-5.116531-13.430894 0-5.326309 ' \
           '1.702782-9.698896 5.116531-13.111622 3.197832-3.40761 7.674796-5.116531 13.430894-5.116531l79.626525 ' \
           '0c7.03523-17.692964 12.791327-27.501354 17.268292-29.420053s9.377578-1.809205 14.710027 0.320295c4.900613 ' \
           '1.918699 8.41874 5.116531 10.553357 9.593496 2.128477 4.691859 1.599428 11.192923-1.599428 ' \
           '19.507286l148.060127 0c5.54018 0 9.91379 1.599428 13.111622 4.797259 3.40761 3.62762 5.116531 8.104585 ' \
           '5.116531 13.430894 0 5.331425-1.708921 9.702989-5.116531 13.111622-3.413749 3.62762-7.78429 ' \
           '5.436826-13.111622 5.436826l-165.008124 0c-0.855484 1.708921-1.708921 3.307326-2.558265 4.797259-9.169847 ' \
           '17.698081-22.494317 38.054711-39.97341 61.0791 0.209778 0.214894 0.320295 0.639566 0.320295 1.279133l0 ' \
           '157.333328c0 6.180769-1.918699 11.192923-5.756097 15.030321-3.197832 3.622504-7.674796 5.541203-13.430894 ' \
           '5.756097-5.54632-0.214894-10.023284-1.918699-13.430894-5.116531-3.62762-4.052293-5.436826-9.274224-5' \
           '.436826-15.669888L626.658366 509.479597C620.47248 515.025916 614.506605 520.032954 608.750508 ' \
           '524.509918zM691.574865 556.488237c-5.756097 ' \
           '0-10.233062-1.703805-13.430894-5.116531-3.413749-3.622504-5.116531-8.099469-5.116531-13.430894 0-5.326309 ' \
           '1.702782-9.698896 5.116531-13.111622 3.197832-3.40761 7.674796-5.116531 13.430894-5.116531l57.881268 ' \
           '0c-4.906753-4.26207-7.78429-9.05933-8.634658-14.390755-1.069355-7.245008 2.342348-13.855566 ' \
           '10.233062-19.826558l55.323003-24.943089c0.423649 0 0.639566-0.639566 ' \
           '0.639566-1.918699-0.215918-0.849344-2.348488-1.279133-6.395664-1.279133l-82.184791 ' \
           '0c-6.395664-0.209778-11.302417-2.0241-14.710027-5.436826-3.197832-3.622504-4.906753-7.780197-5.116531-12' \
           '.472056 0.423649-5.541203 2.238994-9.698896 5.436826-12.472056 3.621481-3.40761 8.41874-5.116531 ' \
           '14.390755-5.116531l120.878045 0c15.559371 0 26.326599 3.307326 32.298614 9.91379 4.686742 5.970992 ' \
           '6.28617 13.221116 4.797259 21.745257-1.918699 7.250124-7.144724 13.111622-15.669888 17.588587l-63.956637 ' \
           '33.897018c-1.49505 0.854461-2.348488 1.388627-2.558265 1.599428-0.215918 0.639566-0.215918 1.069355 0 ' \
           '1.279133 4.476965 3.197832 8.738012 7.144724 12.791327 11.83249l66.195631 0c5.54018 0 9.91379 1.599428 ' \
           '13.111622 4.797259 3.40761 3.62762 5.116531 8.104585 5.116531 13.430894 0 5.331425-1.708921 ' \
           '9.702989-5.116531 13.111622-3.413749 3.62762-7.78429 5.436826-13.111622 5.436826l-44.13008 0c5.326309 ' \
           '16.418948 6.076392 32.617885 2.238994 48.607044-4.692882 13.001105-12.261255 24.088628-22.705118 ' \
           '33.257451-7.890714 6.820336-18.86772 10.657734-32.93818 11.512195-16.628726 ' \
           '0-34.646078-2.988054-54.04387-8.953929-7.03523-1.069355-12.261255-3.837398-15.669888-8.314363-2.988054-4' \
           '.691859-4.053316-10.023284-3.197832-15.989159 0.849344-5.756097 3.302209-10.023284 7.355525-12.791327 ' \
           '4.686742-2.77316 10.553357-3.731998 17.588587-2.87856 14.919804 5.116531 27.285436 7.995091 37.09485 ' \
           '8.634658 10.872628 0.209778 18.228153-1.708921 22.065552-5.756097 4.261047-4.476965 7.139607-9.702989 ' \
           '8.634658-15.669888 1.279133-11.512195-1.069355-22.065552-7.03523-31.659047L691.574865 556.488237z" ' \
           'p-id="2663"></path></svg> '

HOTKEY_PATH = os.path.join(base_dir, 'hotkey_info.json')

KEY_PATH = os.path.join(base_dir, 'key.json')


class KeyListen(QThread):
    key_changed = pyqtSignal(list, int, int)

    def __init__(self, *args, **kwargs):
        super(KeyListen, self).__init__(*args, **kwargs)
        self._init_arguments()
        self.is_run = False

    def _init_arguments(self):
        self.key_list = []
        self.hm = pyWinhook.HookManager()
        self.mouse_listen = False
        self.key_listen = True

        self.hm.KeyUp = self.key_up
        self.hm.KeyDown = self.key_down

    def key_down(self, event):
        key = event.KeyID
        if key not in self.key_list: self.key_list.append(key)
        self.key_changed.emit(self.key_list, key, 0)
        return True

    def key_up(self, event):
        key = event.KeyID
        if key in self.key_list: self.key_list.remove(key)
        self.key_changed.emit(self.key_list, 0, key)
        return True

    def run(self):
        # 循环监听
        pythoncom.PumpMessages()

    def start(self, **kwargs):
        if self.key_listen:
            self.hm.HookKeyboard()
        if self.mouse_listen:
            self.hm.HookMouse()
        super(KeyListen, self).start(**kwargs)

    def stop(self):
        if self.key_listen:
            self.hm.UnhookKeyboard()
        if self.mouse_listen:
            self.hm.UnhookMouse()


class Binder:
    __keybinds = defaultdict(dict)
    __keygrabs = defaultdict(int)  # Key grab key -> number of grabs

    setting_flag = False

    key_win32 = {
        '160': 4,
        '161': 4,
        '162': 2,
        '163': 2,
        '164': 1,
        '165': 1,
        '91': 8,
    }  # 主键值

    def __init__(self):
        # Register os dependent hooks
        if sys.platform.startswith("win"):
            self.user32 = ctypes.WinDLL('user32', use_errno=True, use_last_error=True)
            # http://msdn.microsoft.com/en-us/library/windows/desktop/ms646309%28v=vs.85%29.aspx
            prototype = WINFUNCTYPE(c_bool, c_int, c_int, UINT, UINT)
            paramflags = (1, 'hWnd', 0), (1, 'id', 0), (1, 'fsModifiers', 0), (1, 'vk', 0)
            self.RegisterHotKey = prototype(('RegisterHotKey', self.user32), paramflags)

            # http://msdn.microsoft.com/en-us/library/windows/desktop/ms646327%28v=vs.85%29.aspx
            prototype = WINFUNCTYPE(c_bool, c_int, c_int)
            paramflags = (1, 'hWnd', 0), (1, 'id', 0)
            self.UnregisterHotKey = prototype(('UnregisterHotKey', self.user32), paramflags)

    def register_hotkey(self, wid, m_key: dict, a_key: int, callback, *args, **kwargs):
        major_key = 0
        if m_key:
            for _ in m_key:
                major_key |= self.key_win32.get(str(_))
        if wid is None:
            wid = 0x0

        # High word = Key code, Low word = Modifiers
        # https://msdn.microsoft.com/en-us/library/windows/desktop/ms646279%28v=vs.85%29.aspx
        # Add MOD_NOREPEAT = 0x4000 to mods, so that keys don't get notified twice
        # This requires VISTA+ operating system
        key_index = a_key << 16 | major_key
        if not self.__keygrabs[key_index] and \
                not self.RegisterHotKey(int(wid), key_index, major_key, a_key):
            logging.warning("Couldn't register hot key!")
            return False

        self.__keybinds[key_index] = {
            'fun': callback,
            'args': args,
            'kwargs': kwargs,
        }
        self.__keygrabs[key_index] += 1
        return True

    def unregister_hotkey(self, wid, m_key: dict, a_key: int):
        major_key = 0
        if m_key:
            for _ in m_key:
                major_key |= self.key_win32.get(str(_))
        key_index = a_key << 16 | major_key

        self.__keybinds.pop(key_index)
        self.__keygrabs.pop(key_index)

        if not self.UnregisterHotKey(c_int(wid), key_index):
            err = "Couldn't unregister hot key '{0}'. Error code = {1}." \
                .format(str(major_key) + str(a_key), GetLastError())
            print(err)
            return False
        return True

    def handler(self, eventType, message):
        WM_HOTKEY_MSG = 0x0312
        msg = ctypes.wintypes.MSG.from_address(message.__int__())
        if eventType == "windows_generic_MSG":
            if msg.message == WM_HOTKEY_MSG:
                if self.setting_flag:
                    return True
                key = msg.lParam
                hotkey_info = self.__keybinds.get(key, {})
                if hotkey_info:
                    try:
                        fun = hotkey_info.get('fun')
                        args = hotkey_info.get('args')
                        kwargs = hotkey_info.get('kwargs')
                        if args and kwargs:
                            fun(*args, **kwargs)
                        elif args:
                            fun(*args)
                        elif kwargs:
                            fun(**kwargs)
                        else:
                            fun()
                    finally:
                        return True
        return False


class WinEventFilter(QAbstractNativeEventFilter):
    def __init__(self, keybinder):
        self.keybinder = keybinder
        super().__init__()

    def nativeEventFilter(self, eventType, message):
        ret = self.keybinder.handler(eventType, message)
        return ret, 0


class MainUi(TM):

    def __init__(self, *args, **kwargs):
        super(MainUi, self).__init__(*args, **kwargs)
        self.binder = Binder()
        self.win_event_filter = WinEventFilter(self.binder)
        self.event_dispatcher = QAbstractEventDispatcher.instance()
        self.event_dispatcher.installNativeEventFilter(self.win_event_filter)
        self.name_hotkey = self.get_hotkey_info()
        self.add_event_info(self.open_hotkey_settings, '打开设置窗口')
        self.binder.setting_flag = False

    def load_hotkey(self):
        self.binder.__keybinds = defaultdict(dict)
        self.binder.__keygrabs = defaultdict(int)
        for name, key_info in self.name_hotkey.items():
            event_info = self.event_info.get(name)
            if event_info:
                m_key = key_info.get('m_id', [])
                a_key = key_info.setdefault('a_id', 0)
                if not a_key: a_key = 0
                if not m_key: m_key = []
                fun = event_info.get('fun')
                args = event_info.get('args', [])
                kwargs = event_info.get('kwargs', {})
                if all([m_key, fun]) or all([a_key, fun]):
                    self.binder.register_hotkey(self.winId(), m_key, a_key, fun, *args, **kwargs)

    def open_hotkey_settings(self):
        try:
            self.ui.close()
        except:
            pass
        self.binder.setting_flag = True
        self.ui = QDialog(self)
        self.ui.setModal(True)
        self.ui.listen_qthread = KeyListen()

        def _init_layout_setting_connect():
            self.ui.tree_widget = QTreeWidget()
            self.ui.edit_line = QLineEdit()
            self.ui.edit_button = QPushButton()
            self.ui.hotkey_name = QLabel()
            self.ui.save_button = QPushButton()
            self.ui.h2_layout = QHBoxLayout()
            self.ui.v1_layout = QVBoxLayout()

            self.ui.h2_layout.addWidget(self.ui.edit_button)
            self.ui.h2_layout.addWidget(self.ui.hotkey_name)
            self.ui.h2_layout.addWidget(self.ui.edit_line)
            self.ui.h2_layout.addWidget(self.ui.save_button)
            self.ui.h2_layout.addSpacerItem(QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum))

            self.ui.v1_layout.addLayout(self.ui.h2_layout)
            self.ui.v1_layout.addWidget(self.ui.tree_widget)

            self.ui.setLayout(self.ui.v1_layout)

            self.ui.edit_button.resize(25, 25)
            self.ui.edit_button.setFlat(True)
            self.ui.edit_button.setMaximumSize(30, 30)
            add_widget_icon(PEN_SVG, self.ui.edit_button, 20, 20)
            self.ui.edit_button.setEnabled(False)

            self.ui.edit_line.setPlaceholderText('快捷键输入')
            self.ui.edit_line.setReadOnly(True)
            self.ui.edit_line.setHidden(True)
            self.ui.hotkey_name.setHidden(True)

            self.ui.save_button.resize(29, 29)
            self.ui.save_button.setFlat(True)
            self.ui.save_button.setMaximumSize(35, 35)
            add_widget_icon(SAVE_SVG, self.ui.save_button, 34, 29)
            self.ui.save_button.setHidden(True)

            self.ui.tree_widget.setHeaderLabels([''])
            self.ui.tree_widget.setMaximumHeight(300)
            self.ui.tree_widget.setHeaderLabels(['名', '', ''])
            self.ui.tree_widget.setColumnWidth(0, 100)
            self.ui.tree_widget.setColumnWidth(1, 100)
            self.ui.tree_widget.setColumnWidth(2, 100)

            self.ui.v1_layout.setSpacing(0)
            self.ui.v1_layout.setContentsMargins(0, 0, 0, 0)

            self.ui.h2_layout.setSpacing(1)
            self.ui.h2_layout.setContentsMargins(0, 0, 0, 0)

            self.ui.tree_widget.clicked.connect(tree_click_fun)
            self.ui.edit_button.clicked.connect(edit_button_click_fun)
            self.ui.listen_qthread.key_changed.connect(key_changed_fun)
            self.ui.save_button.clicked.connect(save_hotkey_button_click_fun)
            get_key_id_short(KEY_PATH)
            if len(self.event_info):
                for info, value in self.event_info.items():
                    item = QTreeWidgetItem(self.ui.tree_widget)
                    item.setText(0, info)
                    item.setText(2, value.get('hot_key', self.name_hotkey.get(info, {}).get('key_str', '')))

            pass

        def key_changed_fun(*args):
            """
                    MOD_ALT = 1
                    MOD_CONTROL = 2
                    MOD_SHIFT = 4
                    MOD_WIN = 8
                    :param args:
                    :return:
                    """
            # 可用功能键 ：Ctrl, Alt, Shift, Win[162, 163, 164, 165, 160, 161, 91, ]
            item = self.ui.tree_widget.currentItem()
            if self.ui.edit_line.isHidden() or not item:
                return
            can_gong_key_list = [162, 163, 164, 165, 160, 161, 91, ]
            keys = args[0]
            m_id, a_id = [], []
            use_dict = {}
            for _ in keys:
                use_dict[_] = get_key_name(_)
                if _ in can_gong_key_list:
                    m_id.append(_)
                else:
                    a_id.append(_)
            key_ = m_id if not a_id else [*m_id, a_id[-1]]
            key_str = [use_dict.get(_) for _ in key_]
            history_key_str = self.ui.edit_line.text().split('+')
            if not key_:
                return
            if args[2] == 0:
                self.ui.edit_line.setText('+'.join(key_str))

                self.ui.m_id = m_id
                if a_id:

                    self.ui.a_id = a_id[-1]
                else:
                    self.ui.a_id = 0
            else:
                for key in key_str:
                    if key not in history_key_str:
                        self.ui.edit_line.setText('+'.join(key_str))
                        self.ui.m_id = self.ui.m_id
                        if a_id:
                            self.ui.a_id = a_id[-1]
                        else:
                            self.ui.a_id = 0
                        break
            judge_save_button_is_enable()

        def get_key_id_short(path):
            try:
                with open(path, 'r') as w:
                    data = json.loads(w.read())
            except FileNotFoundError:
                data = {}
            self.ui.key_id = data.get('key_id', {})
            self.ui.id_key = dict(zip(self.ui.key_id.values(), self.ui.key_id.keys()))
            self.ui.key_short = data.get('key_short', {})
            self.ui.id_short = data.get('id_short', {})

        def get_key_name(_id):
            key_name = self.ui.id_short.get(str(_id))
            if not key_name: key_name = self.ui.id_key.get(_id)
            if not key_name: key_name = str(_id)
            return key_name

        def add_widget_icon(path, widget, width=None, height=None):
            if os.path.exists(path):
                pixmap = QPixmap(path)
            else:
                if isinstance(path, str):
                    path = bytes(path, encoding='utf-8')
                pixmap = QPixmap()
                pixmap.loadFromData(path)
            icon = QIcon()
            icon.addPixmap(pixmap)
            widget.setIcon(icon)
            if width and height:
                widget.setIconSize(QSize(width, height))

        def tree_click_fun():
            item = self.ui.tree_widget.currentItem()
            if not item:
                return
            name = item.text(0)
            self.ui.hotkey_name.setText(name)
            self.ui.a_id = 0
            self.ui.m_id = []
            self.ui.edit_line.setText(item.text(2))
            judge_save_button_is_enable()

        def judge_save_button_is_enable():
            item = self.ui.tree_widget.currentItem()
            if not item:
                return
            name = item.text(0)
            line_str = self.ui.edit_line.text()
            info = self.name_hotkey.get(name, {})
            if info.get('key_str') == line_str:
                self.ui.save_button.setEnabled(False)
            else:
                self.ui.save_button.setEnabled(True)
            self.ui.edit_button.setEnabled(True)

        def edit_button_click_fun():
            item = self.ui.tree_widget.currentItem()
            if not item:
                return
            self.ui.hotkey_name.setHidden(False)
            self.ui.edit_line.setHidden(False)
            self.ui.save_button.setHidden(False)

            self.ui.hotkey_name.setText(item.text(0))
            self.ui.edit_line.setText(item.text(2))
            self.ui.listen_qthread.start()

        def save_hotkey_button_click_fun():
            item = self.ui.tree_widget.currentItem()
            if not item: return
            name = item.text(0)
            line_str = self.ui.edit_line.text()
            info = self.name_hotkey.get(name, {})
            if info.get('key_str') == line_str: return
            key_list = self.ui.m_id if not self.ui.a_id else [*self.ui.m_id, self.ui.a_id]
            key_str_list = [
                get_key_name(_) for _ in key_list
            ]
            key_str = '+'.join(key_str_list)
            self.name_hotkey[name] = {
                'm_id': self.ui.m_id,
                'a_id': self.ui.a_id,
                'key_str': key_str
            }
            item.setText(2, key_str)
            self.ui.tree_widget.setCurrentItem(None)
            self.ui.edit_line.clear()
            self.ui.edit_line.setHidden(True)
            self.ui.hotkey_name.setHidden(True)
            self.ui.save_button.setHidden(True)
            self.ui.listen_qthread.stop()
            self.save_hotkey_info(self.name_hotkey)
            self.load_hotkey()

        _init_layout_setting_connect()
        self.ui.show()
        self.ui.exec_()
        self.binder.setting_flag = False

    def add_event_info(self, fun, name: str, *args, **kwargs):
        self.event_info[name] = {
            'name': name,
            'fun': fun,
            'args': args,
            'kwargs': kwargs,
        }
        self.load_hotkey()

    def get_hotkey_info(self) -> dict:  # self.name_hotkey = self.get_hotkey_info
        try:
            with open(HOTKEY_PATH, 'r') as f:
                return json.loads(f.read())
        except Exception as e:
            with open(HOTKEY_PATH, 'w') as f:
                f.write(json.dumps({}))
            return {}

    def save_hotkey_info(self, name_hotkey):
        try:
            with open(HOTKEY_PATH, 'w') as f:
                f.write(json.dumps(name_hotkey))
        except Exception as e:
            logging.warning(str(e))

    def closeEvent(self, a0):
        sys.exit(0)


class Test(QMainWindow, MainUi):

    def __init__(self, *args, **kwargs):
        super(Test, self).__init__(*args, **kwargs)
        self.button = QPushButton(self, text='click')
        self.button.clicked.connect(self.open_)
        self.add_event_info(self.test_1, '测试1', 1)
        self.add_event_info(self.test_1, '测试2', 2)
        self.add_event_info(self.test_1, '测试3', num=3)

    def open_(self):
        self.open_hotkey_settings()

    def test_1(self, num):
        QMessageBox.warning(self, '测试', str(num), buttons=QMessageBox.Ok)



if __name__ == '__main__':

    app = QApplication(sys.argv)
    main_ui = Test()
    main_ui.show()
    sys.exit(app.exec_())
