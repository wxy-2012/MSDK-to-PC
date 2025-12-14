from OpenDJI import OpenDJI

import cv2
import numpy as np

"""
在这个示例中，你将看到如何使用 OpenDJI 类，
在主函数中同步检索无人机图像。

    按 Q - 关闭程序
"""

# 连接的安卓设备的IP地址
IP_ADDR = "192.168.208.223"

# 无人机传回的图像可能很大，
#  使用这个来缩小图像：
SCALE_FACTOR = 0.5

# 创建空白帧
BLANK_FRAME = np.zeros((1080, 1920, 3))
BLNAK_FRAME = cv2.putText(BLANK_FRAME, "No Image", (200, 300),
                          cv2.FONT_HERSHEY_PLAIN, 10,
                          (255, 255, 255), 10)

# 连接到无人机
with OpenDJI(IP_ADDR) as drone:
    # 按 'q' 关闭程序
    print("Press 'q' to close the program")
    while cv2.waitKey(20) != ord('q'):

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