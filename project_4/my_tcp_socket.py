import socket


class MyTcpSocket:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        self.host = None
        self.port = None
        self.timeout = 60

    def settimeout(self, new_timeout):
        self.timeout = new_timeout

    def send(self, data_to_send):
        pass

    def recv(self, bytes_to_recv):
        pass

    def close(self):
        pass
