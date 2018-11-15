from ipaddress import IPv4Address
from random import randint
from sys import platform
from time import sleep, time

import socket

from tcp_helper import build_syn_packet, parse_tcp_header_response

_IP_MIN_HEADER_SIZE = 20
class MyTcpSocket:
    def __init__(self):
        if platform != 'linux':
            raise Exception("This code will only work on Linux!")

        self.sending_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)

        # TODO: Find out how to properly create receiving socket, open for connections
        self.receiving_socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.IPPROTO_IP)
        
        self.src_host = self._resolve_local_ip()
        self.src_port = randint(10000, 65535)
        self.dst_host = None
        
        self.dst_port = None
        self.timeout = 60
        self.is_connected = False

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

        self.sending_socket.connect((self.dst_host, self.dst_port))

        start_time = time()
        while True:
            # Kill loop if we're taking too long
            diff = time() - start_time
            if diff > self.timeout:
                break

            # Send SYN
            # TODO: Do something with syn number
            host_ip = int(IPv4Address(self.src_host))
            dest_ip = int(IPv4Address(self.dst_host))
            syn_packet, syn_num  = \
                build_syn_packet(host_ip, self.src_port,
                                dest_ip, self.dst_port, self.timeout)

            self.sending_socket.sendall(syn_packet)

            # Recieve SYN/ACK
            # Receiving socket will handle IP, so this will be the TCP header
            tcp_packet_header = self.receiving_socket.recv(20)
            src_port, dest_port, syn_num, ack_num, flags, window_size, checksum = \
                parse_tcp_header_response(tcp_packet_header)

            # Receieve the rest of the packet
            rest_of_packet = self.receiving_socket.recv()

            # TODO: Verify checksum
            if src_port != self.src_port and dest_port != port:
                # This TCP packet was meant for someone else, try again
                continue

            # send ACK

            # We did everything successfully! End the loop
            self.is_connected = True
            break
        
        # We were unable to connect within the timeout
        raise Exception("Failed to connect within timeout")

    def settimeout(self, new_timeout):
        self.timeout = new_timeout

    def send(self, data_to_send):
        pass

    def recv(self, bytes_to_recv):
        ip_header_bytes = self.receiving_socket.recv(_IP_MIN_HEADER_SIZE)


    def close(self):
        # send FIN
        # TODO: Or FIN/ACK
        self.sending_socket.close()
        self.receiving_socket.close()
        self.is_connected = False
        pass


if __name__ == "__main__":
    # BUG: If a MyTcpSocket object is named socket, gethostbyname will fail
    s = MyTcpSocket()
    s.connect(("35.237.70.67", 80))

