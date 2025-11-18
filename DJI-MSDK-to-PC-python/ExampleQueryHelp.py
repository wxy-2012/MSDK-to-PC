from OpenDJI import OpenDJI

"""
在这个示例中，你将看到如何使用 'help' (帮助) 功能。
帮助功能可以帮助用户查找并理解 MSDK 提供的可用指令。
"""

# 连接的安卓设备的IP地址
IP_ADDR = "10.0.0.6"

# 连接到无人机
with OpenDJI(IP_ADDR) as drone:
    # 获取可用模块列表
    list_modules = drone.getModules()[1:-1].replace('"', '').split(",")
    print("Modules :", list_modules)
    print()

    # 获取模块内的可用键 (key) 列表
    list_keys = drone.getModuleKeys(OpenDJI.MODULE_BATTERY)[1:-1].replace('"', '').split(",")
    print("Module Keys :", sorted(list_keys))
    print()

    # 获取特定键 (key) 的信息
    key_info = drone.getKeyInfo(OpenDJI.MODULE_FLIGHTCONTROLLER, "AircraftLocation3D")
    print("Key Info :")
    print(key_info)

    print()