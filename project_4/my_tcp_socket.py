from ipaddress import IPv4Address
from os import geteuid, system
from random import randint
from sys import platform
from time import sleep, time

import socket

from tcp_helper import build_syn_packet, parse_tcp_header_response, build_ack_packet

_MIN_HEADER_SIZE = 20
_MAX_TCP_PACKET_SIZE = 65535

class MyTcpSocket:
    def __init__(self, debug=False):
        # Make sure we're superuser on linux
        if platform != 'linux':
            raise Exception("This code will only work on Linux!")

        if geteuid() != 0:
            raise Exception("You must be running as superuser for this to work!")

        # Might as well do the IPtables thing since we're in sudo
        system("sudo iptables -A OUTPUT -p tcp --tcp-flags RST RST -j DROP")

        self.sending_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)

        # TODO: Find out how to properly create receiving socket, read connection from it
        self.receiving_socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.IPPROTO_IP)

        self.debug = True

        self.src_host = self._resolve_local_ip()
        self.src_port = randint(10000, 65535)
        if self.debug:
            print("constructor: Host is", self.src_host, "at port", self.src_port)

        self.dst_host = None
        self.dst_port = None
        self.timeout = 60
        self.is_connected = False


    @staticmethod
    def _resolve_local_ip():
        # TODO: This is hacky and definitely not allowed. Replace it!
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('4.2.0.69', 1337))
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

            host_ip = int(IPv4Address(self.src_host))
            dest_ip = int(IPv4Address(self.dst_host))

            # Send SYN
            syn_packet = build_syn_packet(host_ip, self.src_port,
                            dest_ip, self.dst_port, self.timeout)
            self.sending_socket.sendall(syn_packet)
            if self.debug:
                print("connect: sent SYN")

            # Recieve SYN/ACK
            # Receiving socket will handle IP, so this will be Transport+
            # (Assuming this will give us the entire TCP packet)
            rest_of_packet = self.receiving_socket.recv(_MAX_TCP_PACKET_SIZE)
            if self.debug:
                print("connect: received a response")

            tcp_packet_header = rest_of_packet[:_MIN_HEADER_SIZE]
            src_port, dest_port, seq_num, ack_num, flags, window_size, checksum = \
                parse_tcp_header_response(tcp_packet_header)

            # TODO: Check if incoming packet is TCP, is SYN/ACK, meant for us, etc
            if self.debug:
                print("connect: parsed TCP header")

            if src_port != self.src_port and dest_port != port:
                # This TCP packet was meant for someone else, try again
                if self.debug:
                    print("connect: Reading someone else's TCP header")
                continue

            # send ACK
            ack_packet = build_ack_packet(host_ip, self.src_port, 
                            dest_ip, self.dst_port, self.timeout, ack_num, None)
            self.sending_socket.sendall(ack_packet)
            if self.debug:
                print("connect: sent ACK packet")

            # We did everything successfully! End the loop
            self.is_connected = True
            if self.debug:
                print("connect: successful")
            return
        
        # We were unable to connect within the timeout
        raise Exception("Failed to connect within timeout")

    def settimeout(self, new_timeout):
        self.timeout = new_timeout

    def send(self, data_to_send):
        # send data
        if self.debug:
            print("send: sent data")

        # receive ACK
        if self.debug:
            print("send: received ACK")
        pass

    def recv(self, bytes_to_recv):
        # receive data
        # TODO: What flags are needed on a data packet?
        # TODO: Handle ordering issues (only if we do HTTP)
        if self.debug:
            print("recv: received data")
        # send ACK

        if self.debug:
            print("recv: sent ACK")
        pass


    def close(self):
        # send FIN/ACK

        # receive ACK

        # wait for server FIN/ACK

        # send ACK

        self.sending_socket.close()
        self.receiving_socket.close()
        self.is_connected = False
        pass


if __name__ == "__main__":
    # BUG: If a MyTcpSocket object is named socket, gethostbyname will fail
    s = MyTcpSocket(True)
    s.connect(("35.237.70.67", 80)) # Apache web server hosted on GCP that
                                    # not using for anything atm. Good for testing!

