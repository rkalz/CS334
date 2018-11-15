from ipaddress import IPv4Address
from random import randint
from time import sleep

import socket

from tcp_helper import build_syn_packet

_IP_MIN_HEADER_SIZE = 20
class MyTcpSocket:
    def __init__(self):

        self.internal_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        self.src_host = self._resolve_local_ip()
        self.src_port = randint(10000, 65535)
        self.dst_host = None
        self.dst_port = None
        self.timeout = 60

    @staticmethod
    def _resolve_local_ip():
        # Ghetto af and not sure if even allowed
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 88))
        my_ip = s.getsockname()[0]
        s.close()
        return my_ip

    def connect(self, host_and_port_tuple):
        host = host_and_port_tuple[0]
        port = host_and_port_tuple[1]

        self.dst_host = socket.gethostbyname(host)
        self.dst_port = port

        self.internal_socket.connect((self.dst_host, self.dst_port))

        # Send SYN
        # TODO: Probably need to save syn and ack nums
        syn_packet, syn_num, ack_num = \
            build_syn_packet(int(IPv4Address(self.src_host)), self.src_port,
                             int(IPv4Address(self.dst_host)), self.dst_port, self.timeout)

        while True:
            self.internal_socket.sendall(syn_packet)
            sleep(1)

        # Recieve SYN/ACK


        # send ACK

    def settimeout(self, new_timeout):
        self.timeout = new_timeout

    def send(self, data_to_send):
        pass

    def recv(self, bytes_to_recv):
        ip_header_bytes = self.internal_socket.recv(_IP_MIN_HEADER_SIZE)


    def close(self):
        # send FIN
        # TODO: Or FIN/ACK
        self.internal_socket.close()
        pass


if __name__ == "__main__":
    # BUG: If a MyTcpSocket object is named socket, gethostbyname will fail
    s = MyTcpSocket()
    s.connect(("35.237.70.67", 80))

