from OpenDJI import OpenDJI

import keyboard
import time

"""
在这个示例中，你可以用键盘控制无人机！
这个示例演示了如何使用 OpenDJI 类来控制无人机。

    按 F - 无人机起飞。
    按 R - 无人机降落。
    按 E - 开启键盘控制（操纵杆禁用）
    按 Q - 关闭键盘控制（操纵杆启用）
    按 X - 关闭程序

    按 W/S - 向上/向下 移动（升降）
    按 A/D - 向左/向右 旋转（偏航控制）
    按 ↑/↓ - 向前/向后 移动（俯仰）
    按 ←/→ - 向左/向右 移动（横滚）
"""

# 连接的安卓设备的 IP 地址
IP_ADDR = "10.0.0.6"

# 移动系数
MOVE_VALUE = 0.03
ROTATE_VALUE = 0.15


# 连接到无人机
with OpenDJI(IP_ADDR) as drone:

    # 按 'x' 关闭程序
    print("按 'x' 关闭程序")
    while not keyboard.is_pressed('x'):

        # 稍微延迟一下，避免向服务器发送过多请求
        time.sleep(0.1)

        # 核心变量
        rcw = 0.0       # 旋转，左水平摇杆（偏航）
        du = 0.0        # 升降，左垂直摇杆（油门）
        lr = 0.0        # 侧向移动，右水平摇杆（横滚）
        bf = 0.0        # 向前移动，右垂直摇杆（俯仰）

        # 根据按键设置核心变量
        if keyboard.is_pressed('a'): rcw = -ROTATE_VALUE
        if keyboard.is_pressed('d'): rcw =  ROTATE_VALUE
        if keyboard.is_pressed('s'): du  = -MOVE_VALUE
        if keyboard.is_pressed('w'): du  =  MOVE_VALUE

        if keyboard.is_pressed('left'):  lr = -MOVE_VALUE
        if keyboard.is_pressed('right'): lr =  MOVE_VALUE
        if keyboard.is_pressed('down'):  bf = -MOVE_VALUE
        if keyboard.is_pressed('up'):    bf =  MOVE_VALUE

        # 发送移动指令，并打印结果
        print(drone.move(rcw, du, lr, bf, True))

        # 特殊指令
        if keyboard.is_pressed('f'): print(drone.takeoff(True))
        if keyboard.is_pressed('r'): print(drone.land(True))
        if keyboard.is_pressed('e'): print(drone.enableControl(True))
        if keyboard.is_pressed('q'): print(drone.disableControl(True))