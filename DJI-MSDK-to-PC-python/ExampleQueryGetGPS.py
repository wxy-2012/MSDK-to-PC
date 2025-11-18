from OpenDJI import OpenDJI

import re

"""
GPS 坐标示例。
"""

# 连接的安卓设备的IP地址
IP_ADDR = "192.168.1.184"

# 用于提取十进制数的正则表达式
NUM_REG = '[-+]?\\d+\\.?\\d*'

# 连接到无人机
with OpenDJI(IP_ADDR) as drone:
    # 获取位置信息
    location3D = drone.getValue(OpenDJI.MODULE_FLIGHTCONTROLLER, "AircraftLocation3D")
    print("Original result :", location3D)

    # # 用于查看正则表达式是否编译的示例
    # location3D = '{"latitude":32.1125,"longitude":34.805,"altitude":20}'

    # 你需要手动检查错误，并解析返回的字符串
    location_pattern = re.compile(
        '{"latitude":(' + NUM_REG + '),' +
        '"longitude":(' + NUM_REG + '),' +
        '"altitude":(' + NUM_REG + ')}')

    # 如果结果匹配正则表达式，则解析它。
    location_match: re.Match = location_pattern.fullmatch(location3D)
    if location_match is not None:

        # 提取位置参数
        latitude = float(location_match.group(1))
        longitude = float(location_match.group(2))
        altitude = float(location_match.group(3))

        # 打印位置参数：
        print("Latitude :", latitude)
        print("longitude :", longitude)
        print("altitude :", altitude)

    # 否则，可能出现了错误。
    else:
        print("Error while receiving GPS coordinates.")

    print()