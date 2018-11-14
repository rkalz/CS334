import struct
from socket import IPPROTO_TCP

_DONT_FRAGMENT = 2
_ADDITIONAL_FRAGMENTS = 1


def _compute_ip_checksum(src_addr, dest_addr, ip_segment):
    # Make segment even length
    if len(ip_segment) & 1:
        ip_segment += 0

    # Build pseudoheader and thing to calc
    pseudo_header = struct.pack(">IIBBH", src_addr, dest_addr, 0, IPPROTO_TCP, len(ip_segment))
    thing_to_calc = pseudo_header + ip_segment
    sum = 0

    for i in range(1, len(thing_to_calc), 2):
        num = (int(thing_to_calc[i-1]) << 8) + int(thing_to_calc[i])
        sum += num

    carry = sum >> 8
    sum += carry

    sum = ~sum

    return sum


def build_ip_header(src_addr, dest_addr, ttl, data):
    version = 4
    ihl = 5

    dscp = 0
    ecn = 0
    total_length = 4 * ihl + len(data)

    identification = 0

    flags = _DONT_FRAGMENT               # TODO: Handle fragmentation in recv
    fragment_offset = 0

    protocol = IPPROTO_TCP
    checksum = 0

    # Struct Notes
    # > - big endian
    # B - 1 byte
    # H - 2 bytes
    # I - 4 bytes
    # s - string

    ver_and_ihl = version << 4 + ihl
    dscp_and_ecn = dscp << 2 + ecn
    flags_and_frag_offset = flags << 13 + fragment_offset

    if data is None:
        incomplete_fragment = struct.pack(">BBHHHBBHHH",
                                          ver_and_ihl, dscp_and_ecn, total_length,
                                          identification, flags_and_frag_offset,
                                          ttl, protocol, checksum,
                                          src_addr,
                                          dest_addr)
    else:
        incomplete_fragment = struct.pack(">BBHHHBBHHHs",
                                          ver_and_ihl,    dscp_and_ecn,          total_length,
                                          identification, flags_and_frag_offset,
                                          ttl,            protocol,              checksum,
                                          src_addr,
                                          dest_addr,
                                          data)

    checksum = _compute_ip_checksum(src_addr, dest_addr, incomplete_fragment)

    if data is None:
        fragment = struct.pack(">BBHHHBBHHH",
                                          ver_and_ihl, dscp_and_ecn, total_length,
                                          identification, flags_and_frag_offset,
                                          ttl, protocol, checksum,
                                          src_addr,
                                          dest_addr)
    else:
        fragment = struct.pack(">BBHHHBBHHHs",
                                          ver_and_ihl,    dscp_and_ecn,          total_length,
                                          identification, flags_and_frag_offset,
                                          ttl,            protocol,              checksum,
                                          src_addr,
                                          dest_addr,
                                          data)

    return fragment


