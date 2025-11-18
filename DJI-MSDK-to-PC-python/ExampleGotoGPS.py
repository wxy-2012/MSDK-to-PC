from OpenDJI import OpenDJI
from OpenDJI import EventListener

import keyboard
import cv2
import numpy as np
import re
import time

"""
在这个示例中，你将获得实时视频反馈，并能够在预定义的GPS位置之间移动无人机。

    按 Q - 关闭程序

    按 W - 起飞
    按 S - 降落

    按 1 - 移动到第一个GPS坐标
    按 2 - 移动到第二个GPS坐标
    按 3 - 移动到第三个GPS坐标
"""

# 标记无人机的GPS坐标
# TODO : 设置期望的GPS位置
POS_GPS_1 = (32.13291, 34.80572,)
POS_GPS_2 = (32.13306, 34.80836,)
POS_GPS_3 = (32.13568, 34.80792,)

# GPS位置阈值 - 无人机必须多接近坐标点才能注册该点。
GPS_threshold = 3.0  # 米

# GPS时间戳阈值 - GPS的有效时间 - 以防GPS信号丢失。
GPS_timestamp_expired = 3.0  # 秒

# 移动系数
MOVE_VALUE = 0.025
ROTATE_VALUE = 0.15

# 连接的安卓设备的IP地址
# TODO : 根据应用程序设置IP地址
IP_ADDR = "192.168.1.184"

# 无人机图像可能很大，
#  使用这个来缩小图像：
SCALE_FACTOR = 0.25

# 设置为true以显示实时的GPS和罗盘数据
DEBUG_OUTPUT = True

################################ 帧监听器 ################################

# 初始化帧为空白帧
frame = np.zeros((1080, 1920, 3))
frame = cv2.putText(frame, "No Image", (200, 300),
                    cv2.FONT_HERSHEY_PLAIN, 10,
                    (255, 255, 255), 10)
frame = cv2.resize(frame, dsize=None,
                   fx=SCALE_FACTOR, fy=SCALE_FACTOR)


# 为视频创建后台监听器
class frameListener(EventListener):

    def onValue(self, _frame):
        """ 当有新帧可用时调用 """
        global frame
        frame = cv2.resize(_frame, dsize=None,
                           fx=SCALE_FACTOR, fy=SCALE_FACTOR)

    def onError(self, ):
        pass


################################# GPS监听器 #################################

p_isSet = False
p_latitude = 0.0  # 度
p_longitude = 0.0  # 度
p_altitude = 0.0  # 米
p_timestamp = 0.0  # 秒

# 用于提取十进制数的正则表达式
NUM_REG = '[-+]?\\d+\\.?\\d*'


# 为GPS位置创建后台监听器
class gpsListener(EventListener):

    def onValue(self, _location3D):
        """ 当有新的GPS坐标可用时调用 """

        # # 查看正则表达式是否编译的示例
        # location3D = '{"latitude":32.1125,"longitude":34.805,"altitude":20}'
        global p_isSet, p_latitude, p_longitude, p_altitude, p_timestamp

        # 解析返回的字符串
        location_pattern = re.compile(
            '{"latitude":(' + NUM_REG + '),' +
            '"longitude":(' + NUM_REG + '),' +
            '"altitude":(' + NUM_REG + ')}')

        # 如果结果匹配正则表达式，则解析它。
        location_match: re.Match = location_pattern.fullmatch(_location3D)
        if location_match is not None:

            # 提取位置参数
            p_isSet = True
            p_latitude = float(location_match.group(1))
            p_longitude = float(location_match.group(2))
            p_altitude = float(location_match.group(3))
            p_timestamp = time.time()

            # 打印位置参数：
            if DEBUG_OUTPUT:
                print(f"Latitude : {p_latitude:.6f}, " +
                      f"longitude : {p_longitude:.6f}, " +
                      f"altitude : {p_altitude:.6f}")

        # 否则，可能出现了错误。
        else:
            if DEBUG_OUTPUT:
                print("Error while receiving GPS coordinates.")

    def onError(self, ):
        # TODO : 更改 onError 的参数
        pass


############################### 罗盘监听器 ###############################

c_isSet = False
c_bearing = 0.0  # 度
c_timestamp = 0.0  # 秒


# 为罗盘创建后台监听器
class compassListener(EventListener):

    def onValue(self, _compass):
        """ 当有新的罗盘测量数据可用时调用 """

        # # 返回消息示例
        # compass = '-12.4'
        global c_isSet, c_bearing, c_timestamp

        try:
            # 提取罗盘测量值
            c_bearing = float(_compass)
            c_timestamp = time.time()
            c_isSet = True

            if DEBUG_OUTPUT:
                print(f"Bearing: {c_bearing:.2f}")

        except:
            if DEBUG_OUTPUT:
                print("Error while receiving compass measurements.")

    def onError(self, ):
        # TODO : 更改 onError 的参数
        pass


################################# GPS导航器 ################################

# 再次移动无人机之间的延迟
COMMANDS_DELAY = 0.5  # 秒

# 地球半径
EARTH_RADIUS = 6371e3  # 米


# 计算两个GPS坐标之间的方位角
# https://www.movable-type.co.uk/scripts/latlong.html
def calc_bearing(latitude_1, longitude_1, latitude_2, longitude_2):
    # 将所有参数转换为弧度
    latitude_1 = np.deg2rad(latitude_1)
    longitude_1 = np.deg2rad(longitude_1)
    latitude_2 = np.deg2rad(latitude_2)
    longitude_2 = np.deg2rad(longitude_2)

    # 反正切参数
    y = np.sin(longitude_2 - longitude_1) * np.cos(latitude_2)
    x = np.cos(latitude_1) * np.sin(latitude_2) - \
        np.sin(latitude_1) * np.cos(latitude_2) * np.cos(longitude_2 - longitude_1)

    # 计算方位角
    theta = np.atan2(y, x)
    theta = np.rad2deg(theta)

    return theta


# 计算两个GPS坐标之间的距离
# https://www.movable-type.co.uk/scripts/latlong.html
def calc_distance(latitude_1, longitude_1, latitude_2, longitude_2):
    # 将所有参数转换为弧度
    latitude_1 = np.deg2rad(latitude_1)
    longitude_1 = np.deg2rad(longitude_1)
    latitude_2 = np.deg2rad(latitude_2)
    longitude_2 = np.deg2rad(longitude_2)

    delta_latitude = latitude_2 - latitude_1
    delta_longitude = longitude_2 - longitude_1

    a = np.sin(delta_latitude / 2) * np.sin(delta_latitude / 2) + \
        np.cos(latitude_1) * np.cos(latitude_2) * \
        np.sin(delta_longitude / 2) ** 2

    distance = EARTH_RADIUS * 2 * np.atan2(np.sqrt(a), np.sqrt(1 - a))
    return distance


# 移动到指定的GPS坐标
def gotoGPS(drone: OpenDJI, latitude: float, longitude: float):
    """
    将无人机移动到期望的GPS位置。

    Args:
        drone (OpenDJI): 要控制的无人机对象。
        latitude (float): 纬度目标。
        longitude (float): 经度目标。

    Return:
        result (bool): 是否成功
    """

    # 检查罗盘和GPS是否可用
    if not c_isSet: return False
    if not p_isSet: return False

    # 启用应用程序控制
    drone.enableControl()

    while calc_distance(p_latitude, p_longitude, latitude, longitude) > GPS_threshold:

        # 检查GPS是否没有更新
        if time.time() - p_timestamp > GPS_timestamp_expired:
            drone.move(0, 0, 0, 0)
            drone.disableControl()
            return False

        # 计算相对方位角
        d_bearing = calc_bearing(p_latitude, p_longitude, latitude, longitude)
        r_bearing = d_bearing - c_bearing

        # 计算相对作用力
        fb_force = np.cos(np.deg2rad(r_bearing)) * MOVE_VALUE
        lr_force = np.sin(np.deg2rad(r_bearing)) * MOVE_VALUE

        # 移动无人机
        drone.move(0, 0, lr_force, fb_force)

        if DEBUG_OUTPUT:
            print(f"MOVE: {fb_force:.3f}, {lr_force:.3f}")

        # 小延迟，避免发送过多移动指令
        time.sleep(COMMANDS_DELAY)

    # 结束无人机移动
    drone.move(0, 0, 0, 0)
    drone.disableControl()
    return True


##################################### 主函数 #####################################

# 连接到无人机
with OpenDJI(IP_ADDR) as drone:
    # 注册视频、GPS和罗盘的后台监听器
    drone.frameListener(frameListener())
    drone.listen(OpenDJI.MODULE_FLIGHTCONTROLLER, "AircraftLocation3D", gpsListener())
    drone.listen(OpenDJA.MODULE_FLIGHTCONTROLLER, "CompassHeading", compassListener())

    # 按 'q' 关闭程序
    print("Press 'q' to close the program")
    while not keyboard.is_pressed('q'):

        # 显示帧
        cv2.imshow("Live video", frame)
        cv2.waitKey(20)  # 设置 50 fps
        # TODO : 处理帧

        # 起飞和降落指令
        if keyboard.is_pressed('w'): print("Takeoff:", drone.takeoff(True))
        if keyboard.is_pressed('s'): print("Land:", drone.land(True))

        # 前往GPS示例
        if keyboard.is_pressed('1'): gotoGPS(drone, *POS_GPS_1)
        if keyboard.is_pressed('2'): gotoGPS(drone, *POS_GPS_2)
        if keyboard.is_pressed('3'): gotoGPS(drone, *POS_GPS_3)