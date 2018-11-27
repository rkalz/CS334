import struct

from ip_helper import build_ip_header
from socket import IPPROTO_TCP

_FIN_FLAG = 1
_SYN_FLAG = 2
_RST_FLAG = 4
_PSH_FLAG = 8
_ACK_FLAG = 16
_URG_FLAG = 32
_ECE_FLAG = 64
_CWR_FLAG = 128
_NS_FLAG = 256

def verify_tcp_checksum(src_addr, dest_addr, tcp_packet, debug=False):
    checksum = compute_tcp_checksum(src_addr, dest_addr, tcp_packet)
    if len(tcp_packet) % 2 != 0:
        checksum += 1
    checksum = checksum % 65536
    if debug and checksum != 0:
        print("verify_tcp_checksum: computed", checksum)
    return checksum == 0

def compute_tcp_checksum(src_addr, dest_addr, tcp_packet):
    # Make segment even length
    if len(tcp_packet) % 2 == 1:
        tcp_packet += b'\x00'

    # Build pseudoheader and thing to calc
    # (Pseudoheader only exists in TCP checksumming)
    pseudo_header = struct.pack(">IIBBH", src_addr, dest_addr, 0, IPPROTO_TCP, len(tcp_packet))
    thing_to_calc = pseudo_header + tcp_packet
    sum = 0

    # Sum of all two byte pairs in thing_to_calc
    for i in range(1, len(thing_to_calc), 2):
        num = (int(thing_to_calc[i-1]) << 8) + int(thing_to_calc[i])
        sum += num

    # Add third byte to bottom two bytes
    carry = sum >> 16
    sum &= 0xFFFF
    sum += carry

    # Perform twos complement and extract bottom two bytes
    sum = ~sum
    sum &= 0xFFFF

    return sum

def _build_tcp_header(flags, src_addr, src_port, dest_addr, dest_port, seq_num, ack_num, data):
    if seq_num is None:
        # If no seq, make one
        seq_num = 0
    if ack_num is None:
        # If no ack, set to zero
        ack_num = 0
    data_offset = 5                      # header_length / 4, we don't need options to send
    window_size = (1 << 16) - 1          
    checksum = 0
    urg_ptr = 0

    offset_and_ns = (data_offset << 4) + (flags & _NS_FLAG)
    flags &= 0xFF                        # Remove NS flag from input flags

    # Calculate the checksum
    incomplete_segment = struct.pack(">HHIIBBHHH",
                                         src_port, dest_port,
                                         seq_num,
                                         ack_num,
                                         offset_and_ns, flags, window_size,
                                         checksum, urg_ptr)
    if data is not None:
        # TCP checksum *does* include data
        incomplete_segment += data

    checksum = compute_tcp_checksum(src_addr, dest_addr, incomplete_segment)
    if len(incomplete_segment) & 1:
        # BUG: Checksum is off by one if the packet length is odd.
        checksum += 1

    segment = struct.pack(">HHIIBBHHH",
                              src_port, dest_port,
                              seq_num,
                              ack_num,
                              offset_and_ns, flags, window_size,
                              checksum, urg_ptr)
    if data is not None:
        segment += data

    return segment


def build_syn_packet(src_addr, src_port, dest_addr, dest_port, ttl):
    syn_tcp_component = \
        _build_tcp_header(_SYN_FLAG, src_addr, src_port, dest_addr, dest_port, None, None, None)
    full_ip_packet = build_ip_header(src_addr, dest_addr, ttl, syn_tcp_component)
    return full_ip_packet

def build_ack_packet(src_addr, src_port, dest_addr, dest_port, ttl, seq_num, ack_num, data):
    ack_tcp_component = \
        _build_tcp_header(_ACK_FLAG, src_addr, src_port, dest_addr, dest_port, seq_num, ack_num, data)
    full_ip_packet = build_ip_header(src_addr, dest_addr, ttl, ack_tcp_component)
    return full_ip_packet

def build_psh_ack_packet(src_addr, src_port, dest_addr, dest_port, ttl, seq_num, ack_num, data):
    ack_tcp_component  = \
        _build_tcp_header(_PSH_FLAG | _ACK_FLAG, src_addr, src_port, dest_addr, dest_port, seq_num, ack_num, data)
    full_ip_packet = build_ip_header(src_addr, dest_addr, ttl, ack_tcp_component)
    return full_ip_packet

def build_fin_ack_packet(src_addr, src_port, dest_addr, dest_port, ttl, seq_num, ack_num):
    fin_ack_tcp_component = \
        _build_tcp_header(_FIN_FLAG | _ACK_FLAG, src_addr, src_port, dest_addr, dest_port, seq_num, ack_num, None)
    full_ip_packet = build_ip_header(src_addr, dest_addr, ttl, fin_ack_tcp_component)
    return full_ip_packet

def build_syn_ack_packet(src_addr, src_port, dest_addr, dest_port, ttl, seq_num, ack_num):
    fin_ack_tcp_component = \
        _build_tcp_header(_SYN_FLAG | _ACK_FLAG, src_addr, src_port, dest_addr, dest_port, seq_num, ack_num, None)
    full_ip_packet = build_ip_header(src_addr, dest_addr, ttl, fin_ack_tcp_component)
    return full_ip_packet
    
def parse_tcp_header_response(data):
    tcp_header = struct.unpack(">HHIIBBHHH", data)

    src_port = tcp_header[0]
    dest_port = tcp_header[1]
    seq_num = tcp_header[2]
    ack_num = tcp_header[3]
    offset_and_ns = tcp_header[4]
    flags = tcp_header[5]
    window_size = tcp_header[6]
    checksum = tcp_header[7]
    # urg_ptr = tcp_header[8]

    return src_port, dest_port, seq_num, ack_num, offset_and_ns, flags, window_size, checksum