from OpenDJI import OpenDJI

import cv2
import numpy as np
import keyboard

"""
在这个示例中，你将看到如何使用 action (动作) 指令。
action 指令与 set (设置) 指令非常相似，
但它更倾向于物理动作，而不是设置参数。
在这个示例中，你将控制相机（更准确地说是云台），
并设置它的朝向。请注意终端的输出！

    按 X - 关闭程序。

    按 A/D - 将相机向左/向右移动 (偏航)
    按 W/S - 将相机向上/向下移动 (俯仰)
    按 Q/E - 将相机向左/向右倾斜 (横滚)
"""

# 连接的安卓设备的IP地址
IP_ADDR = "10.0.0.6"

# 无人机传回的图像可能很大，
#  使用这个来缩小图像：
SCALE_FACTOR = 0.25

# 创建空白帧
BLANK_FRAME = np.zeros((1080, 1920, 3))
BLNAK_FRAME = cv2.putText(BLANK_FRAME, "No Image", (200, 300),
                          cv2.FONT_HERSHEY_PLAIN, 10,
                          (255, 255, 255), 10)

# 控制角度
ANGLE_STEP = 0.3
pitch = 0.0
roll = 0.0
yaw = 0.0

# 连接到无人机
with OpenDJI(IP_ADDR) as drone:
    # 按 'x' 关闭程序
    print("Press 'x' to close the program")
    while cv2.waitKey(20) != ord('x'):

        # 获取帧
        frame = drone.getFrame()

        # 用键盘控制云台方向
        if keyboard.is_pressed("a"): yaw -= ANGLE_STEP
        if keyboard.is_pressed("d"): yaw += ANGLE_STEP
        if keyboard.is_pressed("q"): roll -= ANGLE_STEP
        if keyboard.is_pressed("e"): roll += ANGLE_STEP
        if keyboard.is_pressed("s"): pitch -= ANGLE_STEP
        if keyboard.is_pressed("w"): pitch += ANGLE_STEP

        # 控制云台的指令，
        # 为什么是这样？这是DJI设计的。
        # 如何知道其他指令是什么样的？
        # 在查询服务器上发送以下指令：
        #   'help Gimbal RotateByAngle'
        # 你可以使用 QueryExampleRaw，或者在这里输入指令：
        #   print(drone.getKeyInfo("Gimbal", "RotateByAngle"))
        command_argument = ('{'
                            '"mode":65535,'
                            f'"pitch":{pitch:5},'
                            f'"roll":{roll:5},'
                            f'"yaw":{yaw:5},'
                            '"pitchIgnored":false,'
                            '"rollIgnored":false,'
                            '"yawIgnored":false,'
                            '"duration":0,'
                            '"jointReferenceUsed":false,'
                            '"timeout":10'
                            '}')

        # 发送动作指令并打印结果，
        # 注意，有些动作不需要值来执行，例如：
        #   drone.action("RemoteController", "RebootDevice")
        print(drone.action(OpenDJI.MODULE_GIMBAL, "RotateByAngle", command_argument))

        # 当没有可用帧时要执行的操作
        if frame is None:
            frame = BLANK_FRAME

        # 调整帧大小 - 可选
        frame = cv2.resize(frame, dsize=None,
                           fx=SCALE_FACTOR,
                           fy=SCALE_FACTOR)

        # 显示帧
        cv2.imshow("Live video", frame)