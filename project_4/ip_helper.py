import struct
from socket import IPPROTO_TCP

_DONT_FRAGMENT = 2
_ADDITIONAL_FRAGMENTS = 1

def verify_ip_checksum(src_addr, dest_addr, ip_segment, debug=False):
    computed_checksum = compute_ip_checksum(src_addr, dest_addr, ip_segment)
    if len(ip_segment) % 2 != 0:
        computed_checksum += 1
    computed_checksum = computed_checksum % 65536
    if debug and computed_checksum != 0:
        print("verify_ip_checksum: computed", computed_checksum)
    return computed_checksum == 0

def compute_ip_checksum(src_addr, dest_addr, ip_segment):
    # Make segment even length
    if len(ip_segment) % 2 == 1:
        ip_segment += b'\x00'

    sum = 0
    # Sum of all two byte pairs in ip_segment
    for i in range(1, len(ip_segment), 2):
        num = (int(ip_segment[i-1]) << 8) + int(ip_segment[i])
        sum += num

    # Add third byte to bottom two bytes
    carry = sum >> 16
    sum &= 0xFFFF
    sum += carry

    # Perform twos complement and extract bottom two bytes
    sum = ~sum
    sum &= 0xFFFF

    return sum

def build_ip_header(src_addr, dest_addr, ttl, data):
    version = 4
    ihl = 5

    dscp = 0
    ecn = 0
    total_length = (4 * ihl) + len(data)

    identification = 0

    flags = _DONT_FRAGMENT               # We don't need to fragment when we're sending data
    fragment_offset = 0

    protocol = IPPROTO_TCP
    checksum = 0

    ver_and_ihl = (version << 4) + ihl
    dscp_and_ecn = (dscp << 2) + ecn
    flags_and_frag_offset = (flags << 13) + fragment_offset

    incomplete_header = struct.pack(">BBHHHBBHII",
                                    ver_and_ihl, dscp_and_ecn, total_length,
                                    identification, flags_and_frag_offset,
                                    ttl, protocol, checksum,
                                    src_addr,
                                    dest_addr)

    # IP Checksum input doesn't include data
    checksum = compute_ip_checksum(src_addr, dest_addr, incomplete_header)

    fragment = struct.pack(">BBHHHBBHII",
                            ver_and_ihl, dscp_and_ecn, total_length,
                            identification, flags_and_frag_offset,
                            ttl, protocol, checksum,
                            src_addr,
                            dest_addr)
    if data is not None:
        fragment += data

    return fragment

def parse_ip_header(data):
    valid_ip_header = struct.unpack(">BBHHHBBHII", data)

    # ver_and_ihl = valid_ip_header[0]
    # dscp_and_ecn = valid_ip_header[1]
    total_length = valid_ip_header[2]
    # identification = valid_ip_header[3]
    # flags_and_frag_offset = valid_ip_header[4]
    # ttl = valid_ip_header[5]
    protocol = valid_ip_header[6]
    # checksum = valid_ip_header[7]
    src_addr = valid_ip_header[8]
    dest_addr = valid_ip_header[9]

    return src_addr, dest_addr, protocol, total_length

