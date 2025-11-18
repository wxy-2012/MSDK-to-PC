from OpenDJI import OpenDJI
from OpenDJI import EventListener

import keyboard
import time

"""
这个示例教你如何在 MSDK 上注册和移除监听器。
在这个具体示例中，监听器用于接收操纵杆位置，
并将其打印在屏幕上。

    按 X - 关闭程序（并移除监听器）。
    玩一下操纵杆，看看会发生什么！
"""

# 连接的安卓设备的IP地址
IP_ADDR = "10.0.0.6"

# 用于保存操纵杆位置的字典 (map)
joystick_position = {
    "LH": 0, "LV": 0,
    "RH": 0, "RV": 0,
}


# EventListener 的演示实现，
#  带有一个额外的构造函数
class MapUpdateListener(EventListener):

    def __init__(self, identifier: str = ""):
        """ 设置此类更新存储在 'identifier' 键中 """
        self._id = identifier

    def onValue(self, value):
        """ 当有新值时，更新 'joystick_position' """
        joystick_position[self._id] = int(value)


# 连接到无人机
with OpenDJI(IP_ADDR) as drone:
    # 注册一些监听器，用于获取操纵杆位置更新
    drone.listen("RemoteController", "StickLeftVertical", MapUpdateListener("LV"))
    drone.listen("RemoteController", "StickLeftHorizontal", MapUpdateListener("LH"))
    drone.listen("RemoteController", "StickRightVertical", MapUpdateListener("RV"))
    drone.listen("RemoteController", "StickRightHorizontal", MapUpdateListener("RH"))

    # 按 'x' 退出
    print("Press 'x' to exit!")
    while not keyboard.is_pressed("x"):
        # 打印操纵杆位置
        print(
            f"LH : {joystick_position['LH']:4} " +
            f"LV : {joystick_position['LV']:4} " +
            f"RH : {joystick_position['RH']:4} " +
            f"RV : {joystick_position['RV']:4} ",
            end='\t\t\r'
        )
        # 休眠一会儿，太频繁的更新容易引发难以排查的错误。
        time.sleep(0.1)  # 100 毫秒 -> 10 赫兹

    # 记住要清理已注册的监听器，
    #  否则控制器最终会溢出。
    drone.unlisten("RemoteController", "StickLeftVertical")
    drone.unlisten("RemoteController", "StickLeftHorizontal")
    drone.unlisten("RemoteController", "StickRightVertical")
    drone.unlisten("RemoteController", "StickRightHorizontal")

    print()