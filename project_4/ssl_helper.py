from os import urandom
import base64
import struct
import subprocess

# Byte layouts taken from https://tls12.ulfheim.net

def generate_x25519_keys():
    # Incredibly cursed crypto keygen
    private_key_pem = subprocess.run(["openssl", "genpkey", "-algorithm", "x25519"], stdout=subprocess.PIPE)
    public_key_pem = subprocess.run(["openssl", "pkey", "-pubout"], stdout=subprocess.PIPE, input=private_key_pem.stdout)

    private_key_pem = private_key_pem.stdout.decode()
    public_key_pem = public_key_pem.stdout.decode()
    if "PRIVATE KEY" not in private_key_pem or "PUBLIC KEY" not in public_key_pem:
        raise Exception("OpenSSL 1.1 is not on this computer!")

    public_key_pem = public_key_pem.replace("-----BEGIN PUBLIC KEY-----\n", '') \
        .replace("\n-----END PUBLIC KEY-----\n", "").encode()
    public_key_pem = base64.decodebytes(public_key_pem)

    public_key = public_key_pem[-32:]

    # OpenSSL command line wants PEM formatted keys. We'll have to build
    # a PEM for an incoming public key (Append "\x30\x2A\x30\x05\x06\x03\x2B\x65\x6E\x03\x21\x00",
    # encode to base64, and add begin and end stuff)
    return public_key, private_key_pem.encode()


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

if __name__ == "__main__":
    public_key_bytes, private_key_pem = generate_x25519_keys()
    print("Public Key:", public_key_bytes)
    print("Private Key:", private_key_pem)
