import struct
from random import randint

from ip_helper import _compute_ip_checksum

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
    data_offset = 5                      # header_length / 4, TODO: Will we need options?
    window_size = (1 << 16) - 1          # TODO: fix this?
    checksum = 0
    urg_ptr = 0                          # TODO: implement URG send?

    offset_and_ns = data_offset << 4 + (flags & _NS_FLAG)
    flags = flags & ((1 << 9) - 1)

    # Calculate the checksum
    # TODO: Are the IP and TCP checksums the same?
    incomplete_segment = struct.pack(">HHIIBBHHHs",
                                     src_port,      dest_port,
                                     syn_num,
                                     ack_num,
                                     offset_and_ns, flags,     window_size,
                                     checksum,      urg_ptr,
                                     data)
    checksum = _compute_ip_checksum(src_addr, dest_addr, incomplete_segment)

    segment = struct.pack(">HHIIBBHHHs",
                          src_port,      dest_port,
                          syn_num,
                          ack_num,
                          offset_and_ns, flags,     window_size,
                          checksum,      urg_ptr,
                          data)

    return segment


def build_syn_packet(src_addr, src_port, dest_addr, dest_port):
    return _build_tcp_header(_SYN_FLAG, src_addr, src_port, dest_addr, dest_port, None, None)