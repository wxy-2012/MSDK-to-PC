import socket
from threading import Thread, Lock, Event
import queue

import av
import av.codec


class EventListener:
    """
    事件监听器 - 用于异步函数的“抽象”类。
    """

    def onValue(self, value: str | None):
        """
        每当值更新时调用。
        """
        raise NotImplementedError("onValue 未实现")


class OpenDJI:
    """
    OpenDJI - MSDK Remote 应用程序的类包装器。
    此类提供了应用程序导出的所有功能，
    获取实时视频流，像操纵杆一样实时控制无人机，
    以及查询无人机/控制器以获取遥测数据或其他用途。
    """

    # 可用模块
    MODULE_GIMBAL = "Gimbal"
    MODULE_REMOTECONTROLLER = "RemoteController"
    MODULE_FLIGHTCONTROLLER = "FlightController"
    MODULE_BATTERY = "Battery"
    MODULE_AIRLINK = "AirLink"
    MODULE_PRODUCT = "Product"
    MODULE_CAMERA = "Camera"

    # 通信通道的预定义端口。
    PORT_VIDEO = 9999
    PORT_CONTROL = 9998
    PORT_QUERY = 9997

    def __init__(self, host: str):
        """
        将此类连接到无人机。给定 'host' IP 地址，构造函数
        会连接到应用程序的所有数据端口。
        IP 可以从应用程序窗口获取。

        Args:
            host (str): 打开了 MSDK Remote 的手机的 IP 地址。
        """

        self.host_address = host

        # 建立网络连接
        self._socket_video = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket_control = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket_query = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            # 尝试连接所有端口
            self._socket_video.connect((self.host_address, self.PORT_VIDEO))
            self._socket_control.connect((self.host_address, self.PORT_CONTROL))
            self._socket_query.connect((self.host_address, self.PORT_QUERY))

        except Exception as e:
            # 出现异常时，关闭所有端口
            self._socket_video.close()
            self._socket_control.close()
            self._socket_query.close()
            raise

        # 此时 - 所有网络均已设置。

        # 设置后台线程
        self._background_frames = BackgroundVideoCodec(self._socket_video)
        self._background_control_messages = BackgroundCommandsQueue(self._socket_control)
        self._background_query_messages = BackgroundCommandListener(self._socket_query)

    ###### 对象处理方法 ######

    # 在 "with OpenDJI(...) as drone:" 这样的命令上调用
    def __enter__(self):
        return self

    # 当 'with' 的作用域结束时调用
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        """
        清理对象，关闭所有通信和线程。
        """
        self._socket_video.close()
        self._socket_control.close()
        self._socket_query.close()

        self._background_frames.stop()
        self._background_control_messages.stop()
        self._background_query_messages.stop()

    ###### 视频方法 ######

    def getFrame(self):
        """
        检索最新的可用帧，如果没有可用帧，则返回 None。
        """
        return self._background_frames.read()

    def frameListener(self, eventHandler: EventListener):
        """
        设置帧监听器 - 一个 EventListener 类，
        将在每个新帧上调用。

        Args:
            eventHandler (EventListener): 一个类，定义了当
                无人机接收到新帧时要执行的操作。
        """
        self._background_frames.registerListener(eventHandler)

    def removeFrameListener(self):
        """
        移除通过 frameListener(listener) 方法设置的帧监听器（如果已设置）。
        """
        self._background_frames.unregisterListener()

    ###### 控制方法 ######

    def send_command(self, sock: socket.socket, command: str) -> None:
        """
        通过套接字发送命令，使用类似 'TELNET' 的协议。

        Args:
            sock (socket.socket): 用于通信的套接字。
            command (str): 要发送的字符串。
        """
        sock.send(bytes(command + '\r\n', 'utf-8'))

    def move(self, rcw: float, du: float, lr: float, bf: float, get_result: bool = False) -> str | None:
        """
        设置无人机移动的作用力 - 参数等同于控制杆的移动。
        所有值都是 -1.0 到 1.0 之间的实数，其中 0.0 是不移动。

        Args:
            rcw (float): 顺时针旋转 (1.0)，或逆时针旋转 (-1.0)。
            du (float): 向下移动 (-1.0) 或向上移动 (1.0)。
            lr (float): 向左移动 (-1.0) 或向右移动 (1.0)。
            bf (float): 向后移动 (-1.0) 或向前移动 (1.0)。
            get_result (bool): 标记是否等待服务器的响应。

        Return:
            如果 get_result 为 true，则返回服务器的消息 (str)，否则返回 None。
        """

        def clip1(value):
            return min(1.0, max(-1.0, value))

        # 确保值在 -1.0 和 1.0 之间
        rcw = clip1(rcw)
        du = clip1(du)
        lr = clip1(lr)
        bf = clip1(bf)

        # 发送命令
        command = f'rc {rcw:.4f} {du:.2f} {lr:.2f} {bf:.2f}'
        self.send_command(self._socket_control, command)

        # 返回结果：
        if get_result:
            return self._background_control_messages.read()
        else:
            self._background_control_messages.disposeNext()

    def enableControl(self, get_result: bool = False) -> str | None:
        """
        启用控制。此命令在进行移动之前至关重要，
        因为此命令会从遥控器获取控制权并将
        无人机的控制权交给应用程序。

        Args:
            get_result (bool): 标记是否等待服务器的响应。

        Return:
            如果 get_result 为 true，则返回服务器的消息 (str)，否则返回 None。
        """
        self.send_command(self._socket_control, "enable")

        # 返回结果：
        if get_result:
            return self._background_control_messages.read()
        else:
            self._background_control_messages.disposeNext()

    def disableControl(self, get_result: bool = False) -> str | None:
        """
        禁用控制。此命令在控制无人机后至关重要，
        因为此命令会从程序中移除控制权，
        并将其交还给遥控器。

        Args:
            get_result (bool): 标记是否等待服务器的响应。

        Return:
            如果 get_result 为 true，则返回服务器的消息 (str)，否则返回 None。
        """
        self.send_command(self._socket_control, "disable")

        # 返回结果：
        if get_result:
            return self._background_control_messages.read()
        else:
            self._background_control_messages.disposeNext()

    def takeoff(self, get_result: bool = False) -> str | None:
        """
        无人机起飞。

        Args:
            get_result (bool): 标记是否等待服务器的响应。

        Return:
            如果 get_result 为 true，则返回服务器的消息 (str)，否则返回 None。
        """
        self.send_command(self._socket_control, "takeoff")

        # 返回结果：
        if get_result:
            return self._background_control_messages.read()
        else:
            self._background_control_messages.disposeNext()

    def land(self, get_result: bool = False) -> str | None:
        """
        无人机降落。

        Args:
            get_result (bool): 标记是否等待服务器的响应。

        Return:
            如果 get_result 为 true，则返回服务器的消息 (str)，否则返回 None。
        """
        self.send_command(self._socket_control, "land")

        # 返回结果：
        if get_result:
            return self._background_control_messages.read()
        else:
            self._background_control_messages.disposeNext()

    ###### 键值(Key-Value)方法 ######

    def getValue(self, module: str, key: str) -> str:
        """
        获取特定键的值。
        此方法是阻塞的，会等待结果。

        Args:
            module (str): 键所在的模块。
            key (str): 要发送 get 查询的键。
        """
        # 发送 'get' 命令并等待结果。
        return self._background_query_messages.readOnce(
            f"{module} {key}",
            f"get {module} {key}"
        )

    def listen(self, module: str, key: str, eventHandler: EventListener) -> None:
        """
        在特定键的值上设置监听器。
        此方法是非阻塞的，一旦设置了监听器，
        它就会返回。

        Args:
            module (str): 键所在的模块。
            key (str): 要发送 get 查询的键。
            eventHandler (EventListener): 在此监听器的新值上调用的监听器。
                必须实现 "onValue(self, value)" ！
        """
        # 设置监听器。
        self._background_query_messages.setListener(
            f"{module} {key}",
            eventHandler
        )
        # 发送命令以 'listen' (监听) 该值。
        self._background_query_messages.send_command(
            f"listen {module} {key}"
        )

    def unlisten(self, module: str, key: str) -> None:
        """
        从特定键中移除监听器。
        此方法是阻塞的，会等待远程端对请求的响应。

        Args:
            module (str): 键所在的模块。
            key (str): 要发送 get 查询的键。
        """
        # 首先在该方法上取消监听，
        result = self._background_query_messages.readOnce(
            f"{module} {key}",
            f"unlisten {module} {key}"
        )
        # 然后从内部字典中移除监听器
        self._background_query_messages.removeListener(
            f"{module} {key}",
        )
        return result

    def setValue(self, module: str, key: str, value: str) -> str:
        """
        为特定键设置值。
        此方法是阻塞的，会等待远程端对请求的响应。

        Args:
            module (str): 键所在的模块。
            key (str): 要发送 get 查询的键。
            value (str): 要在所需键上设置的值。
        """
        # 发送 set 请求并等待结果。
        return self._background_query_messages.readOnce(
            f"{module} {key}",
            f"set {module} {key} {value}"
        )

    def action(self, module: str, key: str, value: None | str = None) -> str:
        """
        在特定键上发送动作。
        此方法是阻塞的，会等待远程端对请求的响应。
        工作原理类似于 'set'，但 DJI 对
        这两种类型进行了区分。

        Args:
            module (str): 键所在的模块。
            key (str): 要发送 get 查询的键。
            value (str): 要在所需键上设置的值。
        """
        # 如果此动作没有值：
        if value is None:
            # 发送 action 请求并等待结果。
            return self._background_query_messages.readOnce(
                f"{module} {key}",
                f"action {module} {key}"
            )

        # 如果此动作有值：
        else:
            # 发送 action 请求并等待结果。
            return self._background_query_messages.readOnce(
                f"{module} {key}",
                f"action {module} {key} {value}"
            )

    def help(self, module: str | None = None, key: str | None = None) -> str:
        """
        发送 'help' (帮助) 命令，可以带或不带模块名称和键。

        Args:
            module (str | None): 需要帮助的模块名称，
                或者 None（如果你想检索可用的模块）。
            key (str | None): 需要帮助的键，
                或者 None 以获取模块的键（如果模块不是 None）。
        """
        # 如果没有模块 - 检索可用的模块。
        if module is None:
            return self._background_query_messages.readUnbound(
                "help"
            )

        # 如果没有键但有模块 - 检索模块可用的键。
        if key is None:
            return self._background_query_messages.readUnbound(
                f"help {module}"
            )

        # 如果有键和模块 - 检索特定键的信息。
        else:
            return self._background_query_messages.readUnbound(
                f"help {module} {key}"
            )

    def getModules(self) -> str:
        """
        获取可用的模块。
        """
        return self.help()

    def getModuleKeys(self, module: str) -> str:
        """
        获取模块内可用的键。

        Args:
            module (str): 需要帮助的模块名称。
        """
        return self.help(module)

    def getKeyInfo(self, module: str, key: str) -> str:
        """
        获取特定键的信息。

        Args:
            module (str): 需要帮助的模块名称。
            key (str): 模块内需要帮助的键名称。
        """
        return self.help(module, key)


class BackgroundCommandListener:
    """
    管理来自应用程序的所有查询。
    帮助设置监听器，一次性获取值，从帮助命令获取消息，
    支持同步和异步。
    """

    def __init__(self, sock: socket.socket):
        """
        初始化来自命令管理器的后台消息接收器。

        Args:
            sock (socket.socket): 从中接收消息的套接字。
        """
        # 内部变量
        self._send_lock = Lock()
        self._sock = sock
        self._live = True

        # 监听器字典
        self._listeners = {}
        self._listeners_lock = Lock()

        # 一次性消息事件的字典。
        self._listeners_onces_event = {}
        self._listeners_onces_result = {}
        self._listeners_onces_lock = Lock()

        # 没有监听器的消息队列
        self._unbound_messages = queue.Queue()
        self._message = ""

        # 启动后台线程
        self._thread = Thread(target=self.__ReadMessages__)
        self._thread.daemon = True
        self._thread.start()

    def __ReadMessages__(self):
        """
        在后台读取消息
        """

        # 当标志为 on 时迭代。
        while self._live:

            # 读取数据，如果套接字关闭则关闭线程。
            try:
                data = self._sock.recv(1 << 20)  # 1MB
                if len(data) == 0:
                    break
            except ConnectionAbortedError:
                break

            # 将数据添加到总消息中，
            #  合并分离到达的消息。
            self._message += data.decode("utf-8")

            # 将所有可用的完整消息添加到队列中
            messages_list = self._message.split("\r\n")

            # 添加剩余的消息以供读取。
            for message in messages_list[:-1]:  # 不包括最后一个。

                # 如果消息以 "{" 开头，它可能是帮助消息，
                # 并且如果它的空格少于两个，则无法提取键，
                # 在这两种情况下，此消息更可能是通用的
                if message.startswith("{") or message.count(" ") < 2:
                    self._unbound_messages.put(message)
                    continue

                # 将消息拆分为 unique_key 和消息本身。
                message_parts = message.split(" ", 2)
                unique_key = message_parts[0] + " " + message_parts[1]
                message_trimed = message_parts[2]

                # 检查是否在 unique_key 上注册了事件
                with self._listeners_onces_lock:
                    if unique_key in self._listeners_onces_event:
                        # 调用事件并移除它（它只注册一次）
                        self._listeners_onces_result[unique_key] = message_trimed
                        self._listeners_onces_event[unique_key].set()
                        del self._listeners_onces_event[unique_key]
                        continue

                # 检查是否在 unique_key 上注册了监听器
                with self._listeners_lock:
                    if unique_key in self._listeners:
                        # 调用事件监听器
                        listener: EventListener = self._listeners[unique_key]
                        listener.onValue(message_trimed)
                        continue

                # 否则，将其注册为未绑定的消息
                self._unbound_messages.put(message)

            # 最后一条消息没有以 '\r\n' 结尾，
            # 如果是，那么 message_list[-1] = ""。
            self._message = messages_list[-1]

    def send_command(self, command: str) -> None:
        """
        通过套接字发送命令，使用类似 'TELNET' 的协议。

        Args:
            command (str): 要发送的字符串。
        """
        with self._send_lock:
            self._sock.send(bytes(command + '\r\n', 'utf-8'))

    def readOnce(self, unique_key: str, command: str) -> str:
        """
        发送命令并等待 unique_key 上的响应

        Args:
            unique_key (str): 要等待事件的键。
            command (str): 等待时要发送的命令。
        """
        event = Event()

        # 注册事件
        with self._listeners_onces_lock:
            # 如果 unique_key 已注册，也等待它
            if unique_key in self._listeners_onces_event:
                event = self._listeners_onces_event[unique_key]
            # 如果没有，注册它并发送命令
            else:
                self._listeners_onces_event[unique_key] = event
                self.send_command(command)

        # 等待事件发生
        event.wait()
        return self._listeners_onces_result[unique_key]

    def readUnbound(self, command: str) -> str:
        """
        读取未绑定的消息，但带有一个命令。

        Args:
            command (str): 等待时要发送的命令。
        """
        self.send_command(command)
        return self._unbound_messages.get()

    def setListener(self, unique_key: str, listener: EventListener) -> None:
        """
        为 unique_key 注册一个监听器

        Args:
            unique_key (str): 要监听的键。
            listener (EventListener): 要注册的监听器。
        """
        with self._listeners_lock:
            self._listeners[unique_key] = listener

    def removeListener(self, unique_key: str) -> None:
        """
        从列表中移除监听器。

        Args:
            unique_key (str): 要移除监听器的键。
        """
        with self._listeners_lock:
            if unique_key in self._listeners:
                del self._listeners[unique_key]

    def stop(self, timeout: float | None = None):
        """
        停止线程。（也关闭套接字）

        Args:
            timeout (float | None): 操作超时时间（秒），
                或 None 表示无限期等待。
        """
        self._live = False
        self._sock.close()
        self._thread.join(timeout)


class BackgroundCommandsQueue:
    """
    在后台读取命令服务器的返回消息。
    帮助处理消息并使消息顺序同步。

    注意：此类与控制服务器一起使用，控制服务器不提供
     关于消息与哪个命令关联的明确信息，
     这有时可能导致误导性消息。

    注意：此类的实现在多线程程序中不保证消息顺序。
     例如，如果 read() 和 disposeNext() 从两个不同的线程调用，
     即使有明确的顺序，也不能保证哪条消息将被读取，
     哪条消息将被丢弃，因为我希望此类实现尽可能简单。

    提示：如果有人想这样实现，你将必须使用另一个锁，
     并添加另一个队列 request_orders，以便保留顺序，
     并且锁将保证从消息队列中读取与
     请求队列同步。
    """

    def __init__(self, sock: socket.socket):
        """
        初始化来自命令管理器的后台消息接收器。

        Args:
            sock (socket.socket): 从中接收消息的套接字。
        """
        # 内部变量
        self._sock = sock
        self._queue = queue.Queue()
        self._live = True
        self._message = ""
        self._dispose = 0
        self._dispose_lock = Lock()

        # 启动后台线程
        self._thread = Thread(target=self.__ReadMessages__)
        self._thread.daemon = True
        self._thread.start()

    def __ReadMessages__(self):
        """
        在后台读取消息
        """

        # 当标志为 on 时迭代。
        while self._live:

            # 读取数据，如果套接字关闭则关闭线程。
            try:
                data = self._sock.recv(1 << 20)  # 1MB
                if len(data) == 0:
                    break
            except ConnectionAbortedError:
                break

            # 将数据添加到总消息中，
            #  合并分离到达的消息。
            self._message += data.decode("utf-8")

            # 将所有可用的完整消息添加到队列中
            messages_list = self._message.split("\r\n")

            # 移除标记为丢弃的消息：
            while len(messages_list) > 1 and self._dispose > 0:
                messages_list.pop(0)
                with self._dispose_lock:
                    self._dispose -= 1

            # 添加剩余的消息以供读取。
            for message in messages_list[:-1]:  # 不包括最后一个。
                self._queue.put(message)

            # 最后一条消息没有以 '\r\n' 结尾，
            # 如果是，那么 message_list[-1] = ""。
            self._message = messages_list[-1]

    def read(self, block: bool = True, timeout: float | None = None) -> str | None:
        """
        尝试从服务器读取消息，具有阻塞机制
        和超时选项。

        Args:
            block (bool): True 阻塞，false 非阻塞。
            timeout (float | None): 设置等待消息的超时时间，
                或 None 表示无限期等待。

        Return:
            最后一条消息的字符串（如果可用），否则为 None。
        """
        try:
            return self._queue.get(block)
        except queue.Empty:
            self.disposeNext()
        return None

    def disposeNext(self):
        """ 设置为丢弃（忽略）下一条接收到的消息。 """
        with self._dispose_lock:
            self._dispose += 1

    def stop(self, timeout: float | None = None):
        """
        停止线程。（也关闭套接字）

        Args:
            timeout (float | None): 操作超时时间（秒），
                或 None 表示无限期等待。
        """
        self._live = False
        self._sock.close()
        self._thread.join(timeout)


class BackgroundVideoCodec:
    """
    在后台捕获帧，
    这样帧处理就不会使程序滞后，
    并且最新的帧将立即返回。

    目前仅以 H264 格式检索帧。
    无人机也支持 H265，但目前未使用。
    如果出现错误，请随时更改编解码器。

    内部使用。
    """

    def __init__(self, sock: socket.socket):
        """
        初始化后台视频编解码器，并立即启动它。
        期望一个打开并连接的套接字以从中检索帧。

        Args:
            sock (socket.socket): 从中接收视频的套接字。
        """
        # 内部变量
        self._sock = sock
        self._frame = None
        self._codec = av.codec.context.CodecContext.create('h264', 'r')
        self._live = True
        self._listener = None

        # 启动后台线程
        self._thread = Thread(target=self.__ReadFrames__)
        self._thread.daemon = True
        self._thread.start()

    def __ReadFrames__(self):
        """
        在后台读取帧
        """

        # 当标志为 on 时迭代。
        while self._live:

            # 读取数据，如果套接字关闭则关闭线程。
            try:
                data = self._sock.recv(1 << 20)  # 1MB
                if len(data) == 0:
                    break
            except ConnectionAbortedError:
                break

            # 遍历数据中的数据包，
            # 并从数据包中解码帧。
            for packet in self._codec.parse(data):
                for frame in self._codec.decode(packet):

                    self._frame = frame.to_ndarray(format='bgr24')

                    # 使用新帧调用监听器
                    #  将监听器保存在新变量中以避免
                    #  多线程错误。
                    listener: EventListener = self._listener

                    if listener:
                        listener.onValue(self._frame)

        # 如果连接/线程中断，则将帧设置为 None。
        self._frame = None

    def read(self):
        """ 从此视频流中获取最后可用的帧。 """
        return self._frame

    def stop(self, timeout: float | None = None):
        """
        停止线程。（也关闭套接字）

        Args:
            timeout (float | None): 操作超时时间（秒），
                或 None 表示无限期等待。
        """
        self._live = False
        self._sock.close()
        self._thread.join(timeout)

    def registerListener(self, listener: EventListener):
        """ 设置帧监听器 """
        self._listener = listener

    def unregisterListener(self):
        """ 移除帧监听器 """
        self._listener = None