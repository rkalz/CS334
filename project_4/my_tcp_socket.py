from ipaddress import IPv4Address
from os import geteuid, system
from random import randint
from sys import platform
from time import sleep, time

import socket

from ip_helper import parse_ip_header, verify_checksum
from tcp_helper import build_syn_packet, parse_tcp_header_response, build_ack_packet

_MIN_HEADER_SIZE = 20
_MAX_TCP_PACKET_SIZE = 65535
_IP_PACKET_START = 14
_TCP_PACKET_START = 35

class MyTcpSocket:
    def __init__(self, debug=False, debug_verbose=False):
        # Make sure we're superuser on linux
        if platform != 'linux':
            raise Exception("This code will only work on Linux!")

        if geteuid() != 0:
            raise Exception("You must be running as superuser for this to work!")

        # Might as well do the IPtables thing since we're in sudo
        system("sudo iptables -A OUTPUT -p tcp --tcp-flags RST RST -j DROP")

        self.sending_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        self.receiving_socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0800))

        self.debug = debug
        self.debug_verbose = debug_verbose

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
        # TODO: This is hacky and probably not allowed. Replace it!
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('4.2.0.69', 1337))
        my_ip = s.getsockname()[0]
        s.close()
        return my_ip

    def _get_next_packet(self):
        # Receiving packet gives us MAC and up
        # We will only check the IP header of this
        # (Correct IP, correct connection type,)
        # and return the beginning of the TCP header
        start_time = time()
        while True:
            diff = time() - start_time
            if diff > self.timeout:
                break

            response_packet = self.receiving_socket.recv(65535)

            # Strip MAC layer and extract IP header
            ip_and_later = response_packet[_IP_PACKET_START:]
            ip_header = ip_and_later[:_MIN_HEADER_SIZE]

            packet_src, packet_dst, packet_type = parse_ip_header(ip_header)
            packet_src_str = str(IPv4Address(packet_src))
            packet_dst_str = str(IPv4Address(packet_dst))
            if packet_type != socket.IPPROTO_TCP or packet_src_str != self.dst_host \
                or packet_dst_str != self.src_host:
                # Not our packet, boss. Wait for another one.
                if self.debug_verbose:
                    print("_get_next_packet: Wrong packet:", packet_src_str, "->", packet_dst_str)
                continue

            checksum_clear = verify_checksum(packet_src, packet_dst, ip_and_later)
            if not checksum_clear:
                # Packet did not pass checksum. 
                # NOTE: Should never happen unless Blackburn does it on purpose
                # Just try again (we should get a retransmission)
                if self.debug_verbose:
                    print("_get_next_packet: IP checksum failed!")
                continue
            
            if self.debug:
                print("_get_next_packet: response received!")
            
            tcp_header_and_data = response_packet[_TCP_PACKET_START:]
            return tcp_header_and_data
               
        
        raise Exception("Failed to receive packet in time!")

    def connect(self, host_and_port_tuple):
        host = host_and_port_tuple[0]
        port = host_and_port_tuple[1]

        self.dst_host = socket.gethostbyname(host)
        self.dst_port = port

        self.sending_socket.connect((self.dst_host, self.dst_port))

        host_ip = int(IPv4Address(self.src_host))
        dest_ip = int(IPv4Address(self.dst_host))

        start_time = time()
        while True:
            # Send SYN
            syn_packet = build_syn_packet(host_ip, self.src_port,
                            dest_ip, self.dst_port, self.timeout)
            self.sending_socket.sendall(syn_packet)
            if self.debug:
                print("connect: sent SYN")

            # Recieve SYN/ACK
            response_packet = self._get_next_packet()
            if self.debug:
                print("connect: received a response")

            tcp_packet_header = response_packet[:_MIN_HEADER_SIZE]
            src_port, dest_port, seq_num, ack_num, flags, window_size, checksum = \
                parse_tcp_header_response(tcp_packet_header)

            # TODO: Check type of incoming packet, checksum, etc

            if src_port != self.dst_port and dest_port != src_port:
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
        
        raise Exception("Failed to receive packet in time!")
        

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
    s = MyTcpSocket(True, True)
    s.connect(("35.237.70.67", 80)) # Apache web server hosted on GCP that
                                    # not using for anything atm. Good for testing!

