from OpenDJI import OpenDJI

import re

"""
在这个示例中，你将看到一个如何从无人机获取信息的简单演示。
这将展示消息是如何被接收和应当如何解析的，在这个示例中，
使用的是遥控器的电池信息。
"""

# 连接的安卓设备的IP地址
IP_ADDR = "10.0.0.6"

# 连接到无人机
with OpenDJI(IP_ADDR) as drone:
    # 获取电池信息
    battery_text = drone.getValue(OpenDJI.MODULE_REMOTECONTROLLER, "BatteryInfo")
    print("原始结果 :", battery_text)

    # 你需要手动检查错误，并解析返回的字符串
    battery_pattern = re.compile(
        '{"enabled":(.+),"batteryPower":(\\d+),"batteryPercent":(\\d+)}')

    # 如果结果匹配正则表达式，则解析它。
    battery_match: re.Match = battery_pattern.fullmatch(battery_text)
    if battery_match is not None:
        # 第一个值是是否启用
        print("是否启用 :", battery_match.group(1))

        # 第二个值是电量 (mah)
        print("电量 :", battery_match.group(2), "mah")

        # 第三个值是百分比
        print("百分比 :", battery_match.group(3), "%")

    print()