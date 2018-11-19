from os import urandom
import struct

# Byte layouts taken from https://tls12.ulfheim.net

def build_client_hello():
    client_version = 0x0303
    client_random = urandom(32)
    session_id = 0

    # Thanks to OpenSSL s_client, we know that the server uses 
    # TLS 1.2 ECDHE-RSA-AES256-GCM-SHA384 (0xC030)
    cipher_suite_bytes = 2
    cipher_suite = 0xC030

    # Disabling compression
    compression_bytes = 0x01
    compression_value = 0

    # Let's see if we can get away with using no extensions
    extensions_length = 0

    # Build client version and later
    client_version_and_later = struct.pack(">H32BBHHBBH", client_version, client_random, session_id,
                                        cipher_suite_bytes, cipher_suite, compression_bytes, compression_value,
                                        extensions_length)
    
    # Build handshake header
    handshake_type = 0x01
    following_bytes = len(client_version_and_later)
    header_and_later = struct.pack(">B3B", handshake_type, following_bytes)
    header_and_later += client_version_and_later

    # Build record header
    record_header_type = 0x16
    protocol_version = 0x0301
    following_bytes = len(header_and_later)
    
    full_hello = struct.pack(">BHH", record_header_type, protocol_version, following_bytes)
    full_hello += header_and_later

    return full_hello
    
