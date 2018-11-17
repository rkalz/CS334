from ipaddress import IPv4Address
from os import geteuid, system
from random import randint
from sys import platform
from time import sleep, time

import socket

from ip_helper import parse_ip_header, verify_checksum
from tcp_helper import build_syn_packet, parse_tcp_header_response, build_ack_packet, \
                        _SYN_FLAG, _ACK_FLAG, _RST_FLAG, build_psh_ack_packet, _PSH_FLAG, \
                        build_fin_ack_packet, _FIN_FLAG

_MIN_HEADER_SIZE = 20
_MAX_TCP_PACKET_SIZE = 65535
_IP_PACKET_START = 14
_TCP_PACKET_START = 20
_MAX_SEQ_ACK_VAL = 0xFFFFFFFF
_IPV4_LOOPBACK_VAL = 2130706433

class MyTcpSocket:
    # TODO: Add additional input parameters to allow creating new client sockets from accept?
    # src and dest parameters will be used by a listener to generate new sockets
    def __init__(self, debug=False, debug_verbose=False, src_host=None, src_port=None, dst_host=None
    , dst_port=None):
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

        self.src_host = src_host
        if self.src_host is None:
            self.src_host = int(IPv4Address(self._resolve_local_ip()))
        
        self.src_port = src_port
        if self.src_port is None:
            # NOTE: Find a way to check if the port is taken, perhaps?
            # The odds of this occuring seem pretty slim, though
            self.src_port = randint(10000, 65535)

        self.dst_host = None
        self.dst_port = None
        self.timeout = 60
        self.is_connected = False

        self.cwnd = 0

        # TODO: Better method of handling this information
        self.last_seq_recv = 0
        self.last_ack_recv = 0
        self.last_data_recv = 0


    @staticmethod
    def _resolve_local_ip():
        # TODO: Make sure that this is allowed
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('4.2.0.69', 1337))
        my_ip = s.getsockname()[0]
        s.close()
        return my_ip

    def _handle_congestion(self, didnt_get_ack=False):
        # Congestion handling rules as defined in the project
        # Reset if an ack fails or we hit 1000
        # Otherwise increment (ACK recevied)
        if self.cwnd == 1000 or didnt_get_ack:
            self.cwnd = 0

        self.cwnd += 1

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
            # (4096 is larger than an Ethernet frame but
            # I don't know the exact number so better
            response_packet = self.receiving_socket.recv(4096)

            # Strip MAC layer and extract IP header
            ip_and_later = response_packet[_IP_PACKET_START:]
            if self.src_host != _IPV4_LOOPBACK_VAL:
                # Remove ethernet padding if not a loopback packet
                ip_and_later = ip_and_later[:-2]
            ip_header = ip_and_later[:_MIN_HEADER_SIZE]

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

            checksum_clear = verify_checksum(packet_src, packet_dst, ip_header)
            if not checksum_clear:
                # Packet did not pass checksum. 
                if self.debug_verbose:
                    print("_get_next_packet: IP checksum failed!")
                if not self.debug and not self.debug_verbose:
                    # Turns out lots of utilities don't send correct checksums
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
                    print("_get_next_packet: Not our packet:", src_port, "->", dest_port)
                continue
            
            checksum_clear = verify_checksum(packet_src, packet_dst, tcp_header_and_data)
            if not checksum_clear:
                # See notes on IP checksum
                if self.debug:
                    print("_get_next_packet: TCP checksum failed!")
                if not self.debug and not self.debug_verbose:
                    # Turns out lots of utilities don't send correct checksums
                    continue
                
            if self.debug:
                print("_get_next_packet: TCP response received")

            if flags & _RST_FLAG:
                # We got a reset signal, the remote port has closed
                if self.debug:
                    print("_get_next_packet: Response was RST!")
                raise Exception("Connection refused")
            
            data = None
            # If there are options, remove them from the data
            offset = offset_and_ns >> 4
            total_header_size = 4 * offset
            data = tcp_header_and_data[total_header_size:]
            if len(data) == 0:
                data = None

            return seq_num, ack_num, flags, data
               
        raise Exception("Connection timeout!")

    def connect(self, host, port):
        if self.is_connected:
            raise Exception("Already connected!")

        host_hostname = socket.gethostbyname(host)
        if host_hostname[:4] == "127.":
            # We're using loopback. Set source to localhost.
            self.src_host = int(IPv4Address("127.0.0.1"))
        if self.debug:
            print("constructor: Host is", str(IPv4Address(self.src_host))
            , "at port", self.src_port)

        self.dst_host = int(IPv4Address(socket.gethostbyname(host)))
        self.dst_port = port

        dst_host_str = str(IPv4Address(self.dst_host))
        self.sending_socket.connect((dst_host_str, self.dst_port))

        start_time = time()
        while True:
            diff = time() - start_time
            if diff > self.timeout:
                break

            # Send SYN (SEQ = 0, ACK = 0)
            syn_packet = build_syn_packet(self.src_host, self.src_port,
                            self.dst_host, self.dst_port, self.timeout)
            self.sending_socket.sendall(syn_packet)

            if self.debug:
                print("connect: sent SYN")

            # Recieve SYN/ACK (SEQ = X, ACK = 1)
            syn_ack_seq_num, syn_ack_ack_num, flags, _ = self._get_next_packet()

            syn_ack_flag = _SYN_FLAG | _ACK_FLAG
            if flags & syn_ack_flag == 0:
                # This isn't a SYN/ACK packet and thus not the packet we're looking for
                # Send a new SYN
                if self.debug:
                    print("connect: did not receieve a SYN/ACK packet")
                continue
            if syn_ack_ack_num != 1:
                # This isn't the ACK we're looking for
                # Send a new SYN
                if self.debug:
                    print("connect: received incorrect ACK! expected",
                    str(1), "got", str(syn_ack_ack_num))
                continue
            
            self.last_seq_recv = syn_ack_seq_num
            self.last_ack_recv = syn_ack_ack_num
            self.last_data_recv = 1
            
            if self.debug:
                print("connect: received SYN/ACK")
            self._handle_congestion()

            # send ACK (SEQ = 1, ACK = X + 1)
            ack_seq_num = 1
            ack_ack_num = (syn_ack_seq_num + 1) % _MAX_SEQ_ACK_VAL
            ack_packet = build_ack_packet(self.src_host, self.src_port, self.dst_host,
                self.dst_port, self.timeout, ack_seq_num, ack_ack_num, None)
            self.sending_socket.sendall(ack_packet)
            if self.debug:
                print("connect: sent ACK packet")

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
        if not self.is_connected:
            raise Exception("Cannot send data on a closed socket!")

        # send data
        data_seq_num = self.last_ack_recv
        data_ack_num = (self.last_seq_recv + self.last_data_recv) % _MAX_SEQ_ACK_VAL 

        start_time = time()
        while True:
            diff = time() - start_time
            if diff > self.timeout:
                raise Exception("Connection timeout")

            # TODO: Handle data that's too large to send in one packet
            # NOTE: Split packets and send all but last with ACK only, send last with PSH/ACK
            # The PSH flag tells the remote that there's no more data to be sent
            data_packet = build_psh_ack_packet(self.src_host, self.src_port, 
                        self.dst_host, self.dst_port, self.timeout, data_seq_num, 
                        data_ack_num, data_to_send)
            self.sending_socket.sendall(data_packet)

            if self.debug:
                print("send: sent data")

            # receive ACK
            ack_seq_num, ack_ack_num, ack_flags, _ = self._get_next_packet()
            if ack_flags != _ACK_FLAG:
                # This isn't an ACK!
                if self.debug:
                    print("send: Packet received, but it wasn't an ACK")
                continue
            if ack_seq_num != data_ack_num and \
                ack_ack_num != (data_seq_num + len(data_to_send)) % _MAX_SEQ_ACK_VAL:
                # The SEQ and ACK numbers aren't correct
                if self.debug:
                    print("send: Received incorrect SEQ and ACK nums")
                continue
            self.last_seq_recv = ack_seq_num
            self.last_ack_recv = ack_ack_num

            self._handle_congestion()
            if self.debug:
                print("send: received ACK")
            return
        
        # Never got our ACK
        self._handle_congestion(True)
        raise Exception("Connection timeout!")

    def recv(self, bytes_to_recv=0):
        # receive data
        # TODO: Handle ordering issues (hopefully not needed for this)
        # See notes in send

        if not self.is_connected:
            raise Exception("Cannot receive data on a closed socket!")

        start_time = time()
        while True:
            diff = time() - start_time
            if diff > self.timeout:
                raise Exception("Connection timeout!")

            data_ack_seq_num, data_ack_ack_num, data_ack_flags, resp_data = \
                self._get_next_packet()
            
            psh_ack_flag = _PSH_FLAG | _ACK_FLAG
            if data_ack_flags != psh_ack_flag:
                # Not a PSH/ACK flag. Keep listening.
                # TODO: Correct format is to keep receiving ACK flagged packets
                # until we get a PSH/ACK. This code will only work for a single packet
                if self.debug:
                    print("recv: Packet received, but it wasn't a PSH ACK")
                continue
            if data_ack_seq_num != self.last_seq_recv and data_ack_ack_num != self.last_ack_recv:
                # SEQ and ACK nums are bad. Keep listening.
                if self.debug:
                    print("recv: Received incorrect SEQ and/or ACK numbers")
                continue
            
            self.last_seq_recv = data_ack_seq_num
            self.last_ack_recv = data_ack_ack_num
            self.last_data_recv = len(resp_data)

            # We got something!
            self._handle_congestion()
            if self.debug:
                print("recv: received data")
            
            # send ACK
            ack_confirm_seq_num = self.last_ack_recv
            ack_confirm_ack_num = (self.last_seq_recv + self.last_data_recv) % _MAX_SEQ_ACK_VAL
            ack_confirm_recv = build_ack_packet(self.src_host, self.src_port, 
                        self.dst_host, self.dst_port, self.timeout, ack_confirm_seq_num, 
                        ack_confirm_ack_num, None)
            self.sending_socket.sendall(ack_confirm_recv)

            if self.debug:
                print("recv: sent ACK")
            pass

            return resp_data
        
        # Never got a FIN/ACK
        self._handle_congestion(True)
        raise Exception("Connection timeout!")


    def close(self):
        if not self.is_connected:
            raise Exception("Cannot close a socket that's already closed!")

        fin_ack_seq_num = self.last_ack_recv
        fin_ack_ack_num = (self.last_seq_recv + self.last_data_recv) % _MAX_SEQ_ACK_VAL

        start_time = time()
        while True:
            diff = time() - start_time
            if diff > self.timeout:
                raise Exception("Connection timeout!")

            # send FIN/ACK (S=X, A=Y)
            fin_ack_to_send = build_fin_ack_packet(self.src_host, self.src_port, self.dst_host, 
                              self.dst_port, self.timeout, fin_ack_seq_num, fin_ack_ack_num)
            self.sending_socket.sendall(fin_ack_to_send)
            if self.debug:
                print("close: FIN/ACK sent")

            # wait for server FIN/ACK (S=Y, A=X+1)
            # NOTE: Is there an ACK between client FIN/ACK and server FIN/ACK?
            # We could just ignore it since the SEQ/ACK nums appear to be the same...
            fin_ack_resp_seq_num, fin_ack_resp_ack_num, fin_ack_resp_flags, _ = self._get_next_packet()
            fin_ack_flag = _FIN_FLAG | _ACK_FLAG
            if not (fin_ack_resp_flags & fin_ack_flag):
                if self.debug:
                    print("close: Packet received but it wasn't FIN/ACK")
                continue
            if fin_ack_resp_seq_num != fin_ack_ack_num \
                and fin_ack_resp_ack_num != (fin_ack_seq_num + 1) % _MAX_SEQ_ACK_VAL:
                if self.debug:
                    print("close: FIN/ACK received but the SEQ/ACK numbers aren't right")
                continue
            if self.debug:
                print("recv: server FIN/ACK received")
            
            self.last_seq_recv = fin_ack_resp_seq_num
            self.last_ack_recv = fin_ack_resp_ack_num
            self._handle_congestion()

            # send ACK (S=X+1, A=Y+1)
            end_ack_seq_num = (fin_ack_seq_num + 1) % _MAX_SEQ_ACK_VAL
            end_ack_ack_num = (fin_ack_ack_num + 1) % _MAX_SEQ_ACK_VAL
            final_ack_packet = build_ack_packet(self.src_host, self.src_port, self.dst_host, 
                              self.dst_port, self.timeout, end_ack_seq_num, end_ack_ack_num, None)
            self.sending_socket.sendall(final_ack_packet)
            if self.debug:
                print("close: final ack sent")

            self.sending_socket.close()
            self.receiving_socket.close()
            self.is_connected = False
            return
        
        self._handle_congestion(True)
        raise Exception("Connection timeout!")


if __name__ == "__main__":
    # BUG: If a MyTcpSocket object is named socket, gethostbyname will fail
    s = MyTcpSocket(True, False)

    # Install netcat and start an echo server with
    # ncat -l 2000 -k -c 'xargs -n1 echo'
    s.connect("127.0.0.1", 2000)

    # NOTE: ncat will not send a response if there is no return symbol at the end
    s.send("hello\r\n".encode())
    resp = s.recv()
    print("Response:", resp)

    # NOTE: Sometimes ncat will send back a PSH/ACK after a data ACK instead of 
    # a non data ACK and then a PSH/ACK. This will appear as spurious retransmission
    # in Wireshark (and a debug messaage here that we got a non-ACK response)
    s.send("there\n".encode())
    resp = s.recv()
    print("Response:", resp)

    s.send("bye!\r\n\r\n".encode())
    resp = s.recv()
    print("Response:", resp)

    s.close()
