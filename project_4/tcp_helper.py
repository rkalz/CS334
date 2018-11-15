import struct
from random import randint

from ip_helper import build_ip_header, _compute_ip_checksum

_FIN_FLAG = 1
_SYN_FLAG = 2
_RST_FLAG = 4
_PSH_FLAG = 8
_ACK_FLAG = 16
_URG_FLAG = 32
_ECE_FLAG = 64
_CWR_FLAG = 128
_NS_FLAG = 256


def _build_tcp_header(flags, src_addr, src_port, dest_addr, dest_port, syn_num, data):
    ack_num = 0
    if syn_num is None:
        # If no syn, make one
        syn_num = randint(0, (1 << 32) - 1)
    else:
        # If syn, set
        ack_num = syn_num + 1
    data_offset = 5                      # header_length / 4, we don't need options to send
    window_size = (1 << 16) - 1          # TODO: fix this?
    checksum = 0
    urg_ptr = 0

    offset_and_ns = (data_offset << 4) + (flags & _NS_FLAG)
    flags &= 0xFF                        # Remove NS flag from flags

    # Calculate the checksum
    # TODO: Are the IP and TCP checksums the same?
    incomplete_segment = struct.pack(">HHIIBBHHH",
                                         src_port, dest_port,
                                         syn_num,
                                         ack_num,
                                         offset_and_ns, flags, window_size,
                                         checksum, urg_ptr)
    if data is not None:
        incomplete_segment += data

    checksum = _compute_ip_checksum(src_addr, dest_addr, incomplete_segment)

    segment = struct.pack(">HHIIBBHHH",
                              src_port, dest_port,
                              syn_num,
                              ack_num,
                              offset_and_ns, flags, window_size,
                              checksum, urg_ptr)
    if data is not None:
        segment += data

    return segment, syn_num, ack_num


def build_syn_packet(src_addr, src_port, dest_addr, dest_port, ttl):
    syn_tcp_component, syn_num, ack_num = \
        _build_tcp_header(_SYN_FLAG, src_addr, src_port, dest_addr, dest_port, None, None)
    full_ip_packet = build_ip_header(src_addr, dest_addr, ttl, syn_tcp_component)
    return full_ip_packet, syn_num, ack_num

def parse_tcp_bytes(data):
    pass