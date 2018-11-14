from socket import socket, AF_INET, SOCK_RAW, SOCK_DGRAM, IPPROTO_RAW, inet_aton, gethostbyname
from random import randint
from time import sleep
from struct import unpack

from tcp_helper import build_syn_packet


class MyTcpSocket:
    def __init__(self):

        self.internal_socket = socket(AF_INET, SOCK_RAW, IPPROTO_RAW)
        self.src_host = self._resolve_local_ip()
        self.src_port = randint(10000, 65535)
        self.dst_host = None
        self.dst_port = None
        self.timeout = 60

    @staticmethod
    def _resolve_local_ip():
        # Ghetto af and not sure if even allowed
        s = socket(AF_INET, SOCK_DGRAM)
        s.connect(('8.8.8.8', 88))
        my_ip = s.getsockname()[0]
        s.close()
        return my_ip

    @staticmethod
    def _ip_to_int(addr):
        return unpack(">I", inet_aton(addr))[0]

    def connect(self, host_and_port_tuple):
        host = host_and_port_tuple[0]
        port = host_and_port_tuple[1]

        self.dst_host = gethostbyname(host)
        self.dst_port = port

        self.internal_socket.connect((self.dst_host, self.dst_port))

        syn_packet, syn_num, ack_num = \
            build_syn_packet(self._ip_to_int(self.src_host), self.src_port,
                             self._ip_to_int(self.dst_host), self.dst_port, self.timeout)
        self.internal_socket.sendall(syn_packet)
        # find syn_ack

        # send ack

    def settimeout(self, new_timeout):
        self.timeout = new_timeout

    def send(self, data_to_send):
        pass

    def recv(self, bytes_to_recv):
        pass

    def close(self):
        self.internal_socket.close()
        pass


if __name__ == "__main__":
    socket = MyTcpSocket()
    while True:
        socket.connect(("35.237.70.67", 80))
        sleep(1)

