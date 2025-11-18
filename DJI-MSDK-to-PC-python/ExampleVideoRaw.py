import socket
import av
import av.codec
import cv2

"""
在这个示例中，你将看到如何使用原始套接字（raw sockets）检索无人机图像，
以及如何将其从字节流处理成帧。

    按 Q - 关闭程序
"""

# 设置 IP 和端口
HOST = '10.0.0.6'
PORT_VIDEO = 9999

# 设置 H264 原始数据的编解码器
codec = av.codec.context.CodecContext.create('h264', 'r')

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sVideo:

    # 连接视频模块
    sVideo.connect((HOST, PORT_VIDEO))

    # 20毫秒的延迟大致等于每秒50帧，
    # 无人机以每秒30帧的速率传输。
    # 按 'q' 关闭程序。
    while cv2.waitKey(20) != ord('q'):

        # 接收原始数据
        data = sVideo.recv(100000)
        if len(data) == 0:
            break

        print('Data size: ', len(data), 'bytes')

        # 将数据解码为数据包 (packets)
        for packet in codec.parse(data):
            # 然后将数据包解码为帧 (frames)
            for frame in codec.decode(packet):

                # 将帧对象转换为 numpy 数组（用于 openCV）
                img = frame.to_ndarray(format = 'bgr24')
                # 稍微调整一下图像大小
                img = cv2.resize(img, None, fx = 0.5, fy = 0.5)
                cv2.imshow('stream', img)