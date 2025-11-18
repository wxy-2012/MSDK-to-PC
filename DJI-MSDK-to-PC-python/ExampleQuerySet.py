from OpenDJI import OpenDJI

import time

"""
在这个示例中，你将看到如何使用 set (设置) 功能。
set 功能需要特定的文本，每个键 (key) 都不同，
应该在 'help' (帮助) 功能（例如 keyInfo）的帮助下获取。
在这个示例中，我们将设置 LED 的行为为关闭 10 秒钟，
然后将它们恢复到原始状态。
"""

# 连接的安卓设备的IP地址
IP_ADDR = "10.0.0.6"

# 连接到无人机
with OpenDJI(IP_ADDR) as drone:
    # 获取 LED 信息
    LEDs_settings_original = drone.getValue("FlightController", "LEDsSettings")
    print("Original result :", LEDs_settings_original)

    # 设置 LED 的指令，
    # 我如何知道指令协议？我使用了这个指令：
    #   print(drone.getKeyInfo("FlightController", "LEDsSettings"))
    LEDs_settings = \
        ('{'
         '"frontLEDsOn":false,'
         '"statusIndicatorLEDsOn":false,'
         '"rearLEDsOn":false,'
         '"navigationLEDsOn":false'
         '}')

    # 尝试设置 LED
    print(drone.setValue("FlightController", "LEDsSettings", LEDs_settings))

    # 再次获取 LED 信息
    LEDs_settings_modified = drone.getValue("FlightController", "LEDsSettings")
    print("Modified result :", LEDs_settings_modified)

    time.sleep(10.0)

    # 最后，为了不伤害任何人（比喻），将原始设置改回去
    print(drone.setValue("FlightController", "LEDsSettings", LEDs_settings_original))
    print()