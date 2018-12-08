#!/usr/bin/env python3

import ssl
from math import floor

import argparse
from my_tcp_socket import MyTcpSocket


def get_my_bytes(host, port, blazerid, is_ssl, debug=False):
    sock = MyTcpSocket(debug=debug)
    if is_ssl:
        print("SSL has been disabled")              

    try:
        sock.connect(host, port)
    except Exception as e:
        print("client: failed to connect", e)
        return

    header = "cs334fall2018"
    response = None
    try:
        # Build and send HELLO message, format response
        # HELLO message construction in here just in case blazerid isn't a string
        hello = header + " HELLO " + blazerid + '\n'
        hello = hello.encode(encoding='ascii')
        if debug:
            print("client: hello sent:", hello)

        sock.send(hello)

        # Convert the response into a list of strings
        response = sock.recv()
        if debug:
            print("client: response received:", response)

        response = response.decode(encoding='ascii')
        response = response[:-1]                        # Strip \n from end of response
        response = response.split(' ')
    except Exception as e:
        # If we get an except Exception as eion, close the socket and return
        print("client: response recv failed:", e)
        sock.close()

    while len(response) == 5 and response[0] == header and response[1] == "STATUS":
        # Make sure we have a correctly formatted STATUS message before handling

        first_number, operator, second_number = None, None, None
        try:
            # Make sure the numbers are actually numbers
            first_number = int(response[2])
            operator = response[3]
            second_number = int(response[4])
        except Exception as e:
            print("client: response parsing failed:", e)
            sock.close()
            get_my_bytes(host, port, blazerid, is_ssl, debug)

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
            if debug:
                print("client: response computation failed")
            sock.close()

        # Build solution message
        challenge_number = str(floor(challenge_number))
        solution = header + ' ' + challenge_number + '\n'
        solution = solution.encode(encoding='ascii')
        if debug:
            print("client: solution sent:", solution)

        try:
            # Send solution message and format the response
            sock.send(solution)

            response = sock.recv()
            if debug:
                print(response)

            response = response.decode(encoding='ascii')
            response = response[:-1]
            response = response.split(' ')
        except Exception as e:
            print("client: solution send failed:", e)
            sock.close()

    if len(response) == 3 and response[0] == header and response[2] == "BYE":
        # If we're out of challenge loop, make sure we have a correctly formatted BYE message
        flag = response[1]
        print(flag)
    else:
        if debug:
            print("client: bad final message", response)
        sock.close()

    sock.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, help="specify a custom port")
    parser.add_argument("-s", "--ssl", help="specify if using ssl", action='store_true')
    parser.add_argument("hostname", type=str, help="specify hostname or IP of server")
    parser.add_argument("blazerid", type=str, help="specify blazerid")
    parser.add_argument("-d", "--debug", help="enable debug printing", action="store_true")

    args = parser.parse_args()

    port = None
    if args.port is not None:
        port = args.port
    elif args.ssl:
        # Default ssl port
        port = 3006
    else:
        # Default port
        port = 3005

    host = None
    if args.hostname.lower() == "cs334":
        host = "192.168.1.2"
    else:
        host = args.hostname

    get_my_bytes(host, port, args.blazerid, args.ssl, args.debug)
