from OpenDJI import OpenDJI
from OpenDJI import EventListener

import cv2
import numpy as np

"""
在这个示例中，你将看到如何使用 OpenDJI 类，
通过监听器异步检索无人机图像。

    按 Q - 关闭程序
"""

# 连接的安卓设备的IP地址
IP_ADDR = "192.168.137.116"

# 无人机传回的图像可能很大，
#  使用这个来缩小图像：
SCALE_FACTOR = 0.5

# 初始化帧为空白帧
frame = np.zeros((1080, 1920, 3))
frame = cv2.putText(frame, "No Image", (200, 300),
                    cv2.FONT_HERSHEY_PLAIN, 10,
                    (255, 255, 255), 10)
frame = cv2.resize(frame, dsize=None,
                   fx=SCALE_FACTOR, fy=SCALE_FACTOR)


# 创建后台监听器
class frameListener(EventListener):

    def onValue(self, _frame):
        """ 当有新帧可用时调用 """
        global frame
        frame = cv2.resize(_frame, dsize=None,
                           fx=SCALE_FACTOR, fy=SCALE_FACTOR)

    def onError(self, ):
        # TODO : 更改 onError 的参数
        pass


# 连接到无人机
with OpenDJI(IP_ADDR) as drone:
    # 注册帧后台监听器
    drone.frameListener(frameListener())
    # 这样做之后，帧将在后台更新

    # 按 'q' 关闭程序
    print("Press 'q' to close the program")
    while cv2.waitKey(20) != ord('q'):
        # 显示帧
        cv2.imshow("Live video", frame)