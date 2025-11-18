import sys
import re  # 导入正则表达式库
# import math  # 不再需要 math 库
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QTimer, QUrl

# 导入 OpenDJI 库
from OpenDJI import OpenDJI


class RealTimeMapApp(QMainWindow):
    def __init__(self):
        super(RealTimeMapApp, self).__init__()
        self.setWindowTitle('无人机实时地图轨迹')  # 修改了标题
        self.resize(1300, 1000)

        layout = QVBoxLayout()

        self.qwebengine = QWebEngineView(self)
        layout.addWidget(self.qwebengine)

        self.container = QWidget(self)
        self.container.setLayout(layout)
        self.setCentralWidget(self.container)

        self.qwebengine.setHtml(self.generate_map_html(), baseUrl=QUrl.fromLocalFile('.'))

        self.new_point = None
        self.old_point = None
        self.old_label = None

        # --- 新增：连接到无人机 ---
        self.drone = None
        try:
            # 连接的安卓设备的IP地址 (从 ExampleQueryGetGPS.py 引用)
            IP_ADDR = "10.201.162.60"  # !! 注意：请确保这是您手机的正确IP
            print(f"正在连接到无人机 @ {IP_ADDR}...")
            self.drone = OpenDJI(IP_ADDR)
            print("连接成功！")

            # 用于提取十进制数的正则表达式 (从 ExampleQueryGetGPS.py 引用)
            NUM_REG = '[-+]?\\d+\\.?\\d*'
            # 用于解析GPS位置的正则表达式
            self.location_pattern = re.compile(
                '{"latitude":(' + NUM_REG + '),' +
                '"longitude":(' + NUM_REG + '),' +
                '"altitude":(' + NUM_REG + ')}')

        except Exception as e:
            print(f"连接到无人机失败: {e}")
            print("程序将以无数据模式运行。")
        # ------------------------

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_map)
        self.timer.start(1000)  # 每秒更新一次 (1000ms)

    def generate_map_html(self):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <title>Real-time Map</title>
            <style>
                body, html, #map {
                    height: 100%;
                    margin: 0;
                }
            </style>
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css">
            <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        </head>
        <body>
            <div id="map" style="width: 100%; height: 100vh;"></div>
            <script>
                // [修改] 将地图中心设置到一个大致的初始位置，例如上海
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
                        if (oldMarker) {
                            pathMarkers.removeLayer(oldMarker);
                        }
                        if (oldLabel) {
                            mymap.removeLayer(oldLabel);
                        }

                        oldMarker = L.marker(latlng, { icon: newMarkerIcon }).addTo(pathMarkers);

                        var label = L.divIcon({
                            className: 'label',
                            html: `<div style="white-space: nowrap; margin-left: 1em;">Lat: ${lat.toFixed(7)} Lng: ${lng.toFixed(7)}</div>`
                        });

                        var newLabel = L.marker(latlng, { icon: label }).addTo(mymap);
                        oldLabel = newLabel;
                    }
                    // 只有在第一次获取坐标时才平移
                    if (!mymap.firstPanDone) {
                        mymap.setView(latlng, 17); // 放大并居中
                        mymap.firstPanDone = true; // 设置一个标志，避免后续一直平移
                    } else {
                        mymap.panTo(latlng); // 后续只平移
                    }
                }
            </script>
        </body>
        </html>
        """
        return html

    def update_map(self):
        # 如果无人机未连接，则不执行任何操作
        if self.drone is None:
            return

        new_point = None
        try:
            # --- 核心修改：从无人机获取实时GPS数据 ---
            # 获取位置信息
            location3D_str = self.drone.getValue(OpenDJI.MODULE_FLIGHTCONTROLLER, "AircraftLocation3D")

            # 解析返回的字符串
            location_match = self.location_pattern.fullmatch(location3D_str)

            if location_match:
                latitude = float(location_match.group(1))
                longitude = float(location_match.group(2))
                altitude = float(location_match.group(3)) # 高度信息暂时不用

                # 检查坐标是否有效（例如，(0,0) 通常是无效数据）
                if abs(latitude) > 0.01 and abs(longitude) > 0.01:
                    new_point = [latitude, longitude]
                else:
                    print("收到无效GPS坐标(0,0)，已忽略。")
            else:
                print(f"GPS数据解析失败。原始数据: {location3D_str}")
            # ----------------------------------------

        except Exception as e:
            print(f"获取GPS时出错: {e}")
            # 发生错误时（例如网络中断），尝试自动重连
            try:
                print("尝试重新连接...")
                IP_ADDR = self.drone.host_address
                self.drone.close()  # 先关闭旧的
                self.drone = OpenDJI(IP_ADDR)
                print("重新连接成功！")
            except Exception as re_e:
                print(f"重连失败: {re_e}")
                self.drone = None  # 彻底标记为断开
            return

        # --- 更新地图 (这部分逻辑与之前相同) ---
        if new_point is None:
            return  # 如果没有有效的新点，则不更新

        if self.new_point is not None:
            self.old_point = self.new_point
        self.new_point = new_point

        # 使用 JavaScript 添加新的轨迹点到地图上
        javascript = f"addPoint({new_point[0]}, {new_point[1]}, true);"
        self.qwebengine.page().runJavaScript(javascript)

        if self.old_point is not None:
            # 使用 JavaScript 添加旧的轨迹点到地图上，并连接成线
            lineCoordinates = "[[" + f"{self.old_point[0]},{self.old_point[1]}], [{new_point[0]},{new_point[1]}]]"
            javascript = f"var line = L.polyline({lineCoordinates}, {{color: 'red'}}).addTo(mymap);"
            self.qwebengine.page().runJavaScript(javascript)

    def closeEvent(self, event):
        """
        重写窗口关闭事件，以确保无人机连接被安全关闭。
        """
        print("正在关闭窗口并断开无人机连接...")
        if self.drone:
            self.drone.close()  # 调用 OpenDJI 的 close 方法
        event.accept()  # 接受关闭事件

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = RealTimeMapApp()
    win.show()
    sys.exit(app.exec_())