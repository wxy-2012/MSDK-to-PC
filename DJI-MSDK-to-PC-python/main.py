import sys
import re
import cv2  # 导入 OpenCV
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QSizePolicy
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QTimer, QUrl, Qt
from PyQt5.QtGui import QImage, QPixmap

# 导入 OpenDJI 库
from OpenDJI import OpenDJI


class RealTimeMapApp(QMainWindow):
    def __init__(self):
        super(RealTimeMapApp, self).__init__()
        self.setWindowTitle('无人机监控终端 - 左侧地图 / 右侧视觉')
        self.resize(2000, 1000)  # 调整宽一点以容纳两个窗口

        # --- 布局设置 ---
        # 使用 QHBoxLayout 实现左右分屏
        main_layout = QHBoxLayout()

        # 1. 左侧：地图
        self.qwebengine = QWebEngineView(self)
        # 设置伸缩因子，例如地图占 1 份
        main_layout.addWidget(self.qwebengine, stretch=1)

        # 2. 右侧：视频显示
        self.video_label = QLabel("等待视频流...", self)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black; color: white; font-size: 20px;")
        self.video_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)  # 允许缩放
        self.video_label.setScaledContents(True)  # 让图片自适应 Label 大小
        # 设置伸缩因子，例如视频占 1 份
        main_layout.addWidget(self.video_label, stretch=1)

        # 容器设置
        self.container = QWidget(self)
        self.container.setLayout(main_layout)
        self.setCentralWidget(self.container)

        # 加载地图
        self.qwebengine.setHtml(self.generate_map_html(), baseUrl=QUrl.fromLocalFile('.'))

        # 变量初始化
        self.new_point = None
        self.old_point = None
        self.old_label = None

        # --- 连接无人机 ---
        self.drone = None
        IP_ADDR = "10.201.162.60"  # 替换为你的实际 IP
        try:
            print(f"正在连接到无人机 @ {IP_ADDR}...")
            self.drone = OpenDJI(IP_ADDR)
            print("连接成功！")

            NUM_REG = '[-+]?\\d+\\.?\\d*'
            self.location_pattern = re.compile(
                '{"latitude":(' + NUM_REG + '),' +
                '"longitude":(' + NUM_REG + '),' +
                '"altitude":(' + NUM_REG + ')}')
        except Exception as e:
            print(f"连接到无人机失败: {e}")

        # --- 定时器设置 ---

        # 1. GPS 地图更新定时器 (低频，例如 1000ms)
        self.timer_gps = QTimer(self)
        self.timer_gps.timeout.connect(self.update_map)
        self.timer_gps.start(1000)

        # 2. 视频流更新定时器 (高频，例如 30ms ~= 33FPS)
        self.timer_video = QTimer(self)
        self.timer_video.timeout.connect(self.update_video)
        self.timer_video.start(30)

    def update_video(self):
        """
        获取视频帧，处理（如YOLO），并显示在右侧
        """
        if self.drone is None:
            return

        # 获取原始帧 (BGR 格式, numpy array)
        frame = self.drone.getFrame()

        if frame is not None:
            # ==========================================
            # [未来扩展区域] 在这里加入你的目标检测代码
            # ==========================================
            # 示例逻辑:
            # results = model(frame) # YOLO 推理
            # frame = plot_boxes(results, frame) # 将框画在 frame 上
            # ==========================================

            # 1. OpenCV 默认是 BGR，Qt 显示需要 RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # 2. 获取图像尺寸
            h, w, ch = frame.shape
            bytes_per_line = ch * w

            # 3. 转换为 Qt 图像格式
            qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

            # 4. 显示在 Label 上
            # 注意：因为设置了 setScaledContents(True)，Label 会自动缩放图片
            self.video_label.setPixmap(QPixmap.fromImage(qt_image))

    def generate_map_html(self):
        # ... (保持原有的 HTML 生成代码不变) ...
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <title>Real-time Map</title>
            <style>
                body, html, #map { height: 100%; margin: 0; }
            </style>
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css">
            <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        </head>
        <body>
            <div id="map" style="width: 100%; height: 100vh;"></div>
            <script>
                var mymap = L.map('map').setView([31.2304, 121.4737], 13); 
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '© OpenStreetMap contributors'
                }).addTo(mymap);
                var pathMarkers = L.layerGroup().addTo(mymap);
                var newMarkerIcon = L.icon({
                    iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
                    iconSize: [25, 41],
                    iconAnchor: [12, 41]
                });
                var oldMarker;
                var oldLabel;
                function addPoint(lat, lng, isNew) {
                    var latlng = new L.LatLng(lat, lng);
                    if (isNew) {
                        if (oldMarker) { pathMarkers.removeLayer(oldMarker); }
                        if (oldLabel) { mymap.removeLayer(oldLabel); }
                        oldMarker = L.marker(latlng, { icon: newMarkerIcon }).addTo(pathMarkers);
                        var label = L.divIcon({
                            className: 'label',
                            html: `<div style="white-space: nowrap; margin-left: 1em;">Lat: ${lat.toFixed(7)} Lng: ${lng.toFixed(7)}</div>`
                        });
                        var newLabel = L.marker(latlng, { icon: label }).addTo(mymap);
                        oldLabel = newLabel;
                    }
                    if (!mymap.firstPanDone) {
                        mymap.setView(latlng, 17);
                        mymap.firstPanDone = true;
                    } else {
                        mymap.panTo(latlng);
                    }
                }
            </script>
        </body>
        </html>
        """
        return html

    def update_map(self):
        # ... (保持原有的 GPS 更新逻辑不变) ...
        if self.drone is None:
            return

        # [为了节省篇幅，此处省略 try-except 块内的原有逻辑，请直接保留你原来的 update_map 代码]
        # 只要确保它是通过 self.timer_gps 调用的即可
        try:
            location3D_str = self.drone.getValue(OpenDJI.MODULE_FLIGHTCONTROLLER, "AircraftLocation3D")
            location_match = self.location_pattern.fullmatch(location3D_str)
            if location_match:
                latitude = float(location_match.group(1))
                longitude = float(location_match.group(2))
                if abs(latitude) > 0.01:
                    new_point = [latitude, longitude]
                    if self.new_point is not None: self.old_point = self.new_point
                    self.new_point = new_point
                    javascript = f"addPoint({new_point[0]}, {new_point[1]}, true);"
                    self.qwebengine.page().runJavaScript(javascript)
                    if self.old_point is not None:
                        lineCoordinates = "[[" + f"{self.old_point[0]},{self.old_point[1]}], [{new_point[0]},{new_point[1]}]]"
                        javascript = f"var line = L.polyline({lineCoordinates}, {{color: 'red'}}).addTo(mymap);"
                        self.qwebengine.page().runJavaScript(javascript)
        except Exception as e:
            print(e)

    def closeEvent(self, event):
        print("正在关闭窗口并断开无人机连接...")
        if self.drone:
            self.drone.close()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = RealTimeMapApp()
    win.show()
    sys.exit(app.exec_())