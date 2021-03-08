from PyQt5.Qt import *


class TM(QObject):  # 主框架
    name_hotkey = {}  # 快捷键信息， 格式：{name:{m_id:[], a_id:0, key_str: Ctrl+A}}

    event_info = {}  # 事件信息 格式： {name:{fun: function, name: xxx, args: args, kwargs: kwargs}}

    def __init__(self, *args, **kwargs):
        super(TM, self).__init__(*args, **kwargs)

    def load_hotkey(self):  # 重新部署快捷键
        pass

    def open_hotkey_settings(self):  # 打开快捷键设置
        pass

    def get_hotkey_info(self) -> dict:  # 获取name_hotkey info
        pass

    def save_hotkey_info(self, name_hotkey):  # 保存 name_hotkey info
        pass

    def add_event_info(self, fun, name: str, *args, **kwargs):  # 添加事件信息 event_info
        pass
