import socket
import keyboard
import time

"""
在这个示例中，你可以用键盘控制无人机！
这个示例演示了如何使用原始套接字（raw sockets）来控制无人机。

    按 F - 无人机起飞。
    按 R - 无人机降落。
    按 E - 开启键盘控制（操纵杆禁用）
    按 Q - 关闭键盘控制（操纵杆启用）
    按 X - 关闭程序

    按 W/S - 向上/向下 移动（升降）
    按 A/D - 向左/向右 旋转（偏航控制）
    按 ↑/↓ - 向前/向后 移动（俯仰）
    按 ←/→ - 向左/向右 移动（横滚）
"""

# 设置 IP 和端口
HOST = '10.0.0.6'
PORT_CONTROL = 9998

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sCommand:
    # 连接控制模块
    sCommand.connect((HOST, PORT_CONTROL))

    # 按 'x' 关闭程序。
    while not keyboard.is_pressed('x'):

        # 稍微延迟一下指令更新，避免向服务器发送过多请求。
        # 100毫秒，意味着10Hz，每秒10条指令。
        time.sleep(0.1)

        # 核心移动变量
        yaw = 0.0  # 偏航
        ascent = 0.0  # 升降
        roll = 0.0  # 横滚
        pitch = 0.0  # 俯仰

        # 移动系数
        rotate_value = 0.1
        move_value = 0.03

        # 根据按键更改移动变量
        if keyboard.is_pressed('a'): yaw = -rotate_value
        if keyboard.is_pressed('d'): yaw = rotate_value
        if keyboard.is_pressed('s'): ascent = -move_value
        if keyboard.is_pressed('w'): ascent = move_value

        if keyboard.is_pressed('left'): roll = -move_value
        if keyboard.is_pressed('right'): roll = move_value
        if keyboard.is_pressed('down'): pitch = -move_value
        if keyboard.is_pressed('up'): pitch = move_value

        # 指令语法示例 : "rc -0.100 0.231 0.000 -0.009"
        command = f'rc {yaw:.2f} {ascent:.2f} {roll:.2f} {pitch:.2f}'

        # 特殊指令
        if keyboard.is_pressed('f'): command = 'takeoff'
        if keyboard.is_pressed('r'): command = 'land'
        if keyboard.is_pressed('e'): command = 'enable'
        if keyboard.is_pressed('q'): command = 'disable'

        # 发送指令
        sCommand.sendall(bytes(command + '\r\n', 'utf-8'))

        # 等待返回消息
        data = sCommand.recv(10000, )
        if len(data) == 0:
            break

        print('数据大小: ', len(data), 'bytes')
        print(data)