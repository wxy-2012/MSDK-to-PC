from OpenDJI import OpenDJI
import cv2
import numpy as np
from ultralytics import YOLO  # 导入 YOLO 库

"""
在这个示例中，我们将无人机的实时视频流传给 YOLO 进行检测，
并显示带有检测框的视频。

    按 Q - 关闭程序
"""

# --- 配置 ---
# 连接的安卓设备的IP地址 (请修改为你手机上显示的IP)
IP_ADDR = "192.168.137.116"
# 你的模型路径 (例如你上传的 last.pt 或官方的 yolo11n.pt)
MODEL_PATH = 'last.pt'
# ------------

# 1. 加载 YOLO 模型
print(f"正在加载模型 {MODEL_PATH} ...")
try:
    model = YOLO(MODEL_PATH)
except Exception as e:
    print(f"模型加载失败: {e}")
    exit()

# 连接到无人机
with OpenDJI(IP_ADDR) as drone:
    print(f"已连接到无人机 @ {IP_ADDR}")
    print("按 'q' 关闭程序")

    while cv2.waitKey(1) != ord('q'):
        # 2. 获取无人机视频帧 (OpenCV BGR 格式)
        frame = drone.getFrame()

        # 如果没有帧，显示黑屏或跳过
        if frame is None:
            # 创建一个黑色背景提示 "No Signal"
            frame = np.zeros((720, 1280, 3), dtype=np.uint8)
            cv2.putText(frame, "Waiting for Frame...", (50, 360),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        else:
            # 3. 使用 YOLO 进行推理
            # stream=True 可以让推理更快，但对于单帧显示直接调用即可
            # conf=0.5 设置置信度阈值
            results = model(frame, verbose=False, conf=0.1)

            # 4. 在帧上绘制检测结果
            # results[0].plot() 会返回一个画好框的 numpy 数组
            annotated_frame = results[0].plot()

            # 将处理后的帧赋值回去，准备显示
            frame = annotated_frame

        # 5. 显示结果
        # 可以在这里调整图像大小以适应屏幕
        frame_show = cv2.resize(frame, (0, 0), fx=0.6, fy=0.6)
        cv2.imshow("Drone YOLO Detection", frame_show)

    cv2.destroyAllWindows()