#!/usr/bin/env python3

import socket
import ssl
from math import floor

import argparse


def get_my_bytes(host, port, blazerid, is_ssl):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    if is_ssl:
        sock = ssl.wrap_socket(sock)                  # The single, magic line that makes this an SSL socket

    try:
        sock.connect((host, port))
    except:
        return

    header = "cs334fall2018"
    response = None
    try:
        # Build and send HELLO message, format response
        # HELLO message construction in here just in case blazerid isn't a string
        hello = header + " HELLO " + blazerid + '\n'
        hello = hello.encode(encoding='ascii')
        sock.send(hello)

        # Convert the response into a list of strings
        response = sock.recv(256)
        response = response.decode(encoding='ascii')
        response = response[:-1]                        # Strip \n from end of response
        response = response.split(' ')
    except:
        # If we get an exception, close the socket and return
        sock.close()
        return

    while len(response) == 5 and response[0] == header and response[1] == "STATUS":
        # Make sure we have a correctly formatted STATUS message before handling

        first_number, operator, second_number = None, None, None
        try:
            # Make sure the numbers are actually numbers
            first_number = int(response[2])
            operator = response[3]
            second_number = int(response[4])
        except:
            sock.close()
            return

        # Compute the response
        challenge_number = None
        if operator == '+':
            challenge_number = first_number + second_number
        elif operator == '-':
            challenge_number = first_number - second_number
        elif operator == '*':
            challenge_number = first_number * second_number
        elif operator == '/' and second_number != 0:
            challenge_number = first_number / second_number
        else:
            sock.close()
            return

        # Build solution message
        challenge_number = str(floor(challenge_number))
        solution = header + ' ' + challenge_number + '\n'
        solution = solution.encode(encoding='ascii')

        try:
            # Send solution message and format the response
            sock.send(solution)

            response = sock.recv(256)
            response = response.decode(encoding='ascii')
            response = response[:-1]
            response = response.split(' ')
        except:
            sock.close()
            return

    if len(response) == 3 and response[0] == header and response[2] == "BYE":
        # If we're out of challenge loop, make sure we have a correctly formatted BYE message
        flag = response[1]
        print(flag)

    sock.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, help="specify a custom port")
    parser.add_argument("-s", "--ssl", help="specify if using ssl", action='store_true')
    parser.add_argument("hostname", type=str, help="specify hostname of server")
    parser.add_argument("blazerid", type=str, help="specify blazerid")

    args = parser.parse_args()

    port = None
    if args.port is not None:
        port = args.port
    elif args.ssl:
        # Default port
        port = 27994
    else:
        # Defaukt ssl port
        port = 27993

    host = None
    if host == "cs334":
        host = "138.26.64.45"
    else:
        host = socket.gethostbyname(args.hostname)

    get_my_bytes(host, port, args.blazerid, args.ssl)
