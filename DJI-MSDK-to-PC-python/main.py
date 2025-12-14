import sys
import re
import cv2  # 导入 OpenCV
import numpy as np
# [修改 1] 导入 QPushButton 以创建按钮
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QSizePolicy, \
    QPushButton
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QTimer, QUrl, Qt
from PyQt5.QtGui import QImage, QPixmap

# 导入 OpenDJI 库
from OpenDJI import OpenDJI


class RealTimeMapApp(QMainWindow):
    def __init__(self):
        super(RealTimeMapApp, self).__init__()
        self.setWindowTitle('无人机监控终端 - 地图 / 视觉 / 控制')
        self.resize(2000, 1100)  # 稍微调高一点高度以容纳底部按钮

        # --- 布局设置 ---

        # [修改 2] 创建根布局 (垂直)，用于上下排列 "内容区" 和 "控制区"
        root_layout = QVBoxLayout()

        # [修改 3] 内容布局 (水平)，用于左右排列 "地图" 和 "视频" (原有的 main_layout)
        content_layout = QHBoxLayout()

        # 1. 左侧：地图
        self.qwebengine = QWebEngineView(self)
        content_layout.addWidget(self.qwebengine, stretch=1)

        # 2. 右侧：视频显示
        self.video_label = QLabel("等待视频流...", self)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black; color: white; font-size: 20px;")
        self.video_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.video_label.setScaledContents(True)
        content_layout.addWidget(self.video_label, stretch=1)

        # 将内容布局加入根布局
        root_layout.addLayout(content_layout, stretch=10)  # 内容区占大部分空间

        # [修改 4] 创建底部控制栏布局
        control_layout = QHBoxLayout()

        # --- 创建控制按钮 ---
        self.btn_takeoff = QPushButton("一键起飞 (Takeoff)")
        self.btn_land = QPushButton("一键降落 (Land)")

        # 设置按钮样式 (起飞绿色，降落红色，字体加大)
        self.btn_takeoff.setStyleSheet(
            "background-color: #28a745; color: white; font-size: 18px; padding: 10px; font-weight: bold; border-radius: 5px;")
        self.btn_land.setStyleSheet(
            "background-color: #dc3545; color: white; font-size: 18px; padding: 10px; font-weight: bold; border-radius: 5px;")

        # 连接按钮点击事件到函数
        self.btn_takeoff.clicked.connect(self.action_takeoff)
        self.btn_land.clicked.connect(self.action_land)

        # 将按钮加入控制栏
        control_layout.addWidget(self.btn_takeoff)
        control_layout.addWidget(self.btn_land)

        # 将控制栏加入根布局
        root_layout.addLayout(control_layout, stretch=1)  # 按钮区占小部分空间

        # 容器设置
        self.container = QWidget(self)
        self.container.setLayout(root_layout)  # 设置为新的根布局
        self.setCentralWidget(self.container)

        # 加载地图
        self.qwebengine.setHtml(self.generate_map_html(), baseUrl=QUrl.fromLocalFile('.'))

        # 变量初始化
        self.new_point = None
        self.old_point = None
        self.old_label = None

        # --- 连接无人机 ---
        self.drone = None
        IP_ADDR = "10.104.16.60"  # 替换为你的实际 IP
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
        self.timer_gps = QTimer(self)
        self.timer_gps.timeout.connect(self.update_map)
        self.timer_gps.start(1000)

        self.timer_video = QTimer(self)
        self.timer_video.timeout.connect(self.update_video)
        self.timer_video.start(30)

    # [修改 5] 添加起飞和降落的逻辑函数
    def action_takeoff(self):
        """执行一键起飞"""
        if self.drone:
            print(">>> 发送起飞指令...")
            # 参考 ExampleControl.py，参数 True 可能表示打印调试信息或确认
            try:
                result = self.drone.takeoff(True)
                print(f"起飞指令返回: {result}")
            except Exception as e:
                print(f"起飞指令发送失败: {e}")
        else:
            print("错误: 无人机未连接")

    def action_land(self):
        """执行一键降落"""
        if self.drone:
            print(">>> 发送降落指令...")
            try:
                result = self.drone.land(True)
                print(f"降落指令返回: {result}")
            except Exception as e:
                print(f"降落指令发送失败: {e}")
        else:
            print("错误: 无人机未连接")

    def update_video(self):
        """获取视频帧，处理并显示"""
        if self.drone is None:
            return

        frame = self.drone.getFrame()

        if frame is not None:
            # OpenCV 默认是 BGR，Qt 显示需要 RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            h, w, ch = frame.shape
            bytes_per_line = ch * w

            qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
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
        if self.drone is None:
            return

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
            # 可以在这里打印错误，或者忽略偶尔的解析错误
            pass

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