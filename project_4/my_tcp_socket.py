from ipaddress import IPv4Address
from os import geteuid, system
from random import randint
from sys import platform
from time import sleep, time

import socket

from ip_helper import parse_ip_header, verify_checksum
from tcp_helper import build_syn_packet, parse_tcp_header_response, build_ack_packet, \
                        _SYN_FLAG, _ACK_FLAG

_MIN_HEADER_SIZE = 20
_MAX_TCP_PACKET_SIZE = 65535
_IP_PACKET_START = 14
_TCP_PACKET_START = 20

class MyTcpSocket:
    def __init__(self, debug=False, debug_verbose=False):
        # Make sure we're superuser on linux
        if platform != 'linux':
            raise Exception("This code will only work on Linux!")

        if geteuid() != 0:
            raise Exception("You must be running as superuser for this to work!")

        # Tell the kernel to not send RST packets back to the remote
        # All packets that this raw socket will see are also passed to the kernel
        # Since our port isn't bound in the OS TCP stack, the OS will assume that the remote
        # is trying to access a closed socket and will then send a RST, which will kill the
        # remote's connection and make us sad
        system("sudo iptables -A OUTPUT -p tcp --tcp-flags RST RST -j DROP")

        self.sending_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)

        # ETH_P_IP (0x0800) - The kernel will give us IP packets
        # The incoming packets will have MAC (but we don't have to check MAC to see if the packets
        # are IP or not)
        self.receiving_socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0800))

        self.debug = debug
        self.debug_verbose = debug_verbose

        self.src_host = int(IPv4Address(self._resolve_local_ip()))
        self.src_port = randint(10000, 65535)
        if self.debug:
            print("constructor: Host is", str(IPv4Address(self.src_host))
            , "at port", self.src_port)

        self.dst_host = None
        self.dst_port = None
        self.timeout = 60
        self.is_connected = False

        self.cwnd = 0
        self.seq_num = 0
        self.ack_num = 0

    @staticmethod
    def _resolve_local_ip():
        # TODO: This is hacky and probably not allowed. Replace it!
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('4.2.0.69', 1337))
        my_ip = s.getsockname()[0]
        s.close()
        return my_ip

    def _handle_congestion(self, didnt_get_ack=False):
        # Congestion handling rules as defined in the project
        # Reset if an ack fails or we hit 1000
        if self.cwnd == 1000 or didnt_get_ack:
            self.cwnd = 0

        self.cwnd += 1

    # TODO: Handle RST in here?
    def _get_next_packet(self):
        # Receiving packet gives us MAC and up
        # We will check both IP and TCP
        # and return relevant TCP information
        start_time = time()
        while True:
            diff = time() - start_time
            if diff > self.timeout:
                break

            # Receive a full ethernet frame
            response_packet = self.receiving_socket.recv(1522)

            # Strip MAC layer, remove ethernet padding bytes, 
            # and extract IP header
            ip_and_later = response_packet[_IP_PACKET_START:-2]
            ip_header = ip_and_later[:_MIN_HEADER_SIZE]

            # TODO: Change ip member variable to int (why do we need to keep it as a string)
            packet_src, packet_dst, packet_type = parse_ip_header(ip_header)
            if packet_type != socket.IPPROTO_TCP or packet_src != self.dst_host \
                or packet_dst != self.src_host:
                # Either it's not TCP, sent by a different source, and/or meant for a 
                # different IP
                if self.debug_verbose:
                    # Find out what packet we picked up for lols
                    packet_type_str = str(packet_type)
                    if packet_type == socket.IPPROTO_TCP:
                        packet_type_str = "TCP"
                    elif packet_type == socket.IPPROTO_UDP:
                        packet_type_str = "UDP"

                    packet_src_str = str(IPv4Address(packet_src))
                    packet_dst_str = str(IPv4Address(packet_dst))
                    packet_type_str = "(" + packet_type_str + ")"
                    print("_get_next_packet: Not our packet:", packet_src_str, "->", packet_dst_str
                    ,packet_type_str)
                continue

            checksum_clear = True
            # checksum_clear = verify_checksum(packet_src, packet_dst, ip_header)
            if not checksum_clear:
                # Packet did not pass checksum. 
                # NOTE: Should never happen unless Blackburn does it on purpose
                # Just try again (we should get a retransmission)
                if self.debug_verbose:
                    print("_get_next_packet: IP checksum failed!")
                continue
            
            # Make sure this is a TCP packet meant for us
            tcp_header_and_data = ip_and_later[_TCP_PACKET_START:]
            tcp_header = tcp_header_and_data[:_MIN_HEADER_SIZE]
            src_port, dest_port, seq_num, ack_num, offset_and_ns, \
            flags, _, _ = parse_tcp_header_response(tcp_header)
                
            if src_port != self.dst_port and dest_port != self.src_port:
                # This isn't our TCP packet. Restart.
                # Multiple sockets connected to the same IP, perhaps?
                if self.debug_verbose:
                    print("_get_next_packet: Not our packet", src_port, "->", dest_port)
                continue
            
            checksum_clear = True
            # checksum_clear = verify_checksum(packet_src, packet_dst, tcp_header_and_data)
            if not checksum_clear:
                # See notes on IP checksum
                if self.debug_verbose:
                    print("_get_next_packet: TCP checksum failed!")
                continue
                
            if self.debug:
                print("_get_next_packet: response received!")

            data = None
            # If there are options, remove them from the data
            offset = offset_and_ns >> 4
            total_header_size = 4 * offset
            if total_header_size > _MIN_HEADER_SIZE:
                data = tcp_header_and_data[total_header_size:]

            return seq_num, ack_num, flags, data
               
        raise Exception("Failed to receive packet in time!")

    def connect(self, host_and_port_tuple):
        host = host_and_port_tuple[0]
        port = host_and_port_tuple[1]

        self.dst_host = int(IPv4Address(socket.gethostbyname(host)))
        self.dst_port = port

        dst_host_str = str(IPv4Address(self.dst_host))
        self.sending_socket.connect((dst_host_str, self.dst_port))

        start_time = time()
        while True:
            diff = time() - start_time
            if diff > self.timeout:
                break

            # Send SYN
            syn_packet, first_seq_num = build_syn_packet(self.src_host, self.src_port,
                            self.dst_host, self.dst_port, self.timeout)
            self.sending_socket.sendall(syn_packet)
            if self.debug:
                print("connect: sent SYN")

            # Recieve SYN/ACK
            seq_num, ack_num, flags, _ = self._get_next_packet()
            if self.debug:
                print("connect: received a response")

            syn_ack_flag = _SYN_FLAG | _ACK_FLAG
            if flags & syn_ack_flag == 0:
                # This isn't a SYN/ACK packet and thus not the packet we're looking for
                # Send a new SYN
                if self.debug:
                    print("connect: did not receieve a SYN/ACK packet")
                continue
            if ack_num != first_seq_num + 1:
                # This isn't the ACK we're looking for
                # Send a new SYN
                if self.debug:
                    print("connect: received incorrect ACK! expected",
                    str(first_seq_num + 1), "got", str(ack_num))
                continue
            self._handle_congestion()

            # send ACK
            ack_packet, seq_num, ack_num = build_ack_packet(self.src_host, self.src_port, self.dst_host,
                self.dst_port, self.timeout, ack_num, seq_num + 1, None)
            self.sending_socket.sendall(ack_packet)
            if self.debug:
                print("connect: sent ACK packet")

            # TODO: Store seq and ack for send and recv

            # We did everything successfully! End the loop
            self.is_connected = True
            if self.debug:
                print("connect: successful")
            return

        self._handle_congestion(True)
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
        # TODO: Handle ordering issues (only if we do HTTP)

        self._handle_congestion()
        if self.debug:
            print("recv: received data")
        # send ACK

        if self.debug:
            print("recv: sent ACK")
        pass


    def close(self):
        # send FIN/ACK

        # receive ACK
        self._handle_congestion()

        # wait for server FIN/ACK
        self._handle_congestion()

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

