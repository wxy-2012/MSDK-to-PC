import cv2
from ultralytics import YOLO
import os

# --- 配置 ---
MODEL_PATH = 'last.pt'
IMG_PATH = 'test.jpg'  # 你的图片路径，或者改成文件夹遍历逻辑
# -----------

def detect_image():
    # 1. 加载模型
    model = YOLO(MODEL_PATH)

    # 2. 读取图片
    img = cv2.imread(IMG_PATH)
    if img is None:
        print(f"无法读取图片: {IMG_PATH}")
        return

    # 3. 进行预测
    # conf=0.5 表示置信度 0.5 以上才算检测到
    results = model(img, conf=0.2)

    # 4. 获取画好框的图片
    # results[0] 对应第一张图的结果
    annotated_img = results[0].plot()

    # --- 进阶：在这里你可以写逻辑 ---
    # 比如：统计检测到了几个物体
    count = len(results[0].boxes)
    print(f"在这张图中检测到了 {count} 个目标")

    if count > 0:
        # 只有检测到物体才保存
        cv2.imwrite('result_detected.jpg', annotated_img)
        print("结果已保存为 result_detected.jpg")
    # -----------------------------

    # 5. 展示图片 (按任意键关闭窗口)
    cv2.imshow("YOLOv8 Detection", annotated_img)
    cv2.waitKey(0) # 0 表示无限等待，直到按键
    cv2.destroyAllWindows()

if __name__ == '__main__':
    detect_image()