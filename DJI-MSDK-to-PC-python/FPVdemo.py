from OpenDJI import OpenDJI

import keyboard
import cv2
import numpy as np

"""
在这个示例中，你可以实时飞行并观看无人机的视频！
就像电脑游戏一样，用键盘移动无人机并在电脑屏幕上看到它的图像！

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

# 连接的安卓设备的IP地址
IP_ADDR = "10.0.0.6"

# 无人机传回的图像可能很大，
#  使用这个来缩小图像：
SCALE_FACTOR = 0.5

# 移动系数
MOVE_VALUE = 0.015
ROTATE_VALUE = 0.15

# 创建空白帧
BLANK_FRAME = np.zeros((1080, 1920, 3))
BLNAK_FRAME = cv2.putText(BLANK_FRAME, "No Image", (200, 300),
                          cv2.FONT_HERSHEY_DUPLEX, 10,
                          (255, 255, 255), 15)

# 连接到无人机
with OpenDJI(IP_ADDR) as drone:
    # 按 'x' 关闭程序
    print("Press 'x' to close the program")
    while not keyboard.is_pressed('x'):

        # 显示无人机的图像
        # 获取帧
        frame = drone.getFrame()

        # 当没有可用帧时要执行的操作
        if frame is None:
            frame = BLANK_FRAME

        # 调整帧大小 - 可选
        frame = cv2.resize(frame, dsize=None,
                           fx=SCALE_FACTOR,
                           fy=SCALE_FACTOR)

        # 显示帧
        cv2.imshow("Live video", frame)
        cv2.waitKey(20)

        # 用键盘移动无人机
        # 核心变量
        yaw = 0.0  # 旋转，左水平摇杆（偏航）
        ascent = 0.0  # 升降，左垂直摇杆（油门）
        roll = 0.0  # 侧向移动，右水平摇杆（横滚）
        pitch = 0.0  # 向前移动，右垂直摇杆（俯仰）

        # 根据按键设置核心变量
        if keyboard.is_pressed('a'): yaw = -ROTATE_VALUE
        if keyboard.is_pressed('d'): yaw = ROTATE_VALUE
        if keyboard.is_pressed('s'): ascent = -MOVE_VALUE
        if keyboard.is_pressed('w'): ascent = MOVE_VALUE

        if keyboard.is_pressed('left'):  roll = -MOVE_VALUE
        if keyboard.is_pressed('right'): roll = MOVE_VALUE
        if keyboard.is_pressed('down'):  pitch = -MOVE_VALUE
        if keyboard.is_pressed('up'):    pitch = MOVE_VALUE

        # 发送移动指令
        drone.move(yaw, ascent, roll, pitch)

        # 特殊指令
        if keyboard.is_pressed('f'): print(drone.takeoff(True))
        if keyboard.is_pressed('r'): print(drone.land(True))
        if keyboard.is_pressed('e'): print(drone.enableControl(True))
        if keyboard.is_pressed('q'): print(drone.disableControl(True))