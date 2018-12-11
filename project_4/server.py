#!/usr/bin/env python3

from my_tcp_socket import MyTcpSocket
from hashlib import sha512
from random import choice, randint
from threading import Thread
from time import sleep

def handle(sock, debug=False, ssl=False):
    hello = sock.recv()
    hello = hello.decode().strip().split(" ")

    if len(hello) != 3 or hello[0] != "cs334fall2018" \
        or hello[1] != "HELLO":
        if debug:
            print("Recevied bad hello: {}".format(hello))
        sock.close()
        return

    name = hello[2]
    if ssl:
        name = name[::-1] # reversed name
    code = sha512(name.encode()).hexdigest()
    challenges_remaining = 100

    first = randint(0, 10000)
    second = randint(1, 10000)
    operation = choice(('+', '-', '*', '/'))
    if operation == '+':
        answer = first + second
    elif operation == '-':
        answer = first - second
    elif operation == '*':
        answer = first * second
    else:
        answer = int(first / second)
    
    while challenges_remaining:
        message_to_send = "cs334fall2018 STATUS {} {} {}\n".format(first, operation, second)
        message_to_send = message_to_send.encode()
        sock.send(message_to_send)

        response = sock.recv()
        response = response.decode().strip().split(" ")
        if len(response) != 2 or response[0] != "cs334fall2018":
            if debug:
                print("Received bad solution: {}".format(response))
            sock.close()
            return
        
        solution = int(response[1])
        if solution == answer:
            challenges_remaining -= 1
            first = randint(0, 10000)
            second = randint(1, 10000)
            operation = choice(('+', '-', '*', '/'))
            if operation == '+':
                answer = first + second
            elif operation == '-':
                answer = first - second
            elif operation == '*':
                answer = first * second
            else:
                answer = int(first / second)
        else:
            if debug:
                print("solution incorrect. expected {} got {}".format(answer, solution))

    done = "cs334fall2018 {} BYE\n".format(code).encode()
    sock.send(done)
    sock.close()
    return

if __name__ == "__main__":
    server_socket = MyTcpSocket()
    server_socket.bind(3005)

    while True:
        new_sock = server_socket.listen()
        Thread(target=handle, args=(new_sock, )).start()