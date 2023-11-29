import socket
import threading
import curses
import time
import fcntl
import struct
import termios
import sys
import paramiko
import numpy as np

from ..game.game import Game
from lanpong.server.ssh import SSHServer


def get_waiting_message():
    rows = Game.DEFAULT_HEIGHT
    cols = Game.DEFAULT_WIDTH

    board = np.full((rows, cols), " ", dtype="S1")
    board[0, :] = board[-1, :] = "-"
    board[:, 0] = board[:, -1] = "|"
    board[0, 0] = board[0, -1] = board[-1, 0] = board[-1, -1] = "+"

    message = "You are player 1. Waiting for player 2..."
    assert len(message) < cols - 2
    start = (cols - len(message)) // 2
    board[rows // 2, start : start + len(message)] = list(message)

    return "\r\n".join(["".join(c.decode() for c in row) for row in board]) + "\r\n"


class Server:
    def __init__(self, key_file_name="test_key") -> None:
        self.server_key = paramiko.RSAKey.from_private_key_file(filename=key_file_name)
        self.connections = []
        self.waiting_message = get_waiting_message()
        self.channel_lock = threading.Lock()

    def start_server(self, host="0.0.0.0", port=2222):
        """Starts an SSH server on specified port and address

        Args:
            host (str): Server host addr. Defaults to '0.0.0.0'.
            port (int): Port. Defaults to 2222.
        """

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((host, port))
            server_sock.listen(100)
            print(f"Listening for connection on {host}:{port}")

            # Accept multiple connections, thread-out
            while True:
                client_socket, client_addr = server_sock.accept()
                print(f"Incoming connection from {client_addr[0]}:{client_addr[1]}")
                client_thread = threading.Thread(
                    target=self.handle_client, args=(client_socket,)
                )
                client_thread.start()

    def broadcast_message(self, message, sender):
        for client in self.connections:
            if client != sender:
                try:
                    client.send(f"Message from {sender.getpeername()}: {message}\r\n")
                except socket.error as e:
                    print(f"Error sending message: {e}\r\n")
                    client.close()
                    self.connections.remove(client)

    def handle_client(self, client_socket):
        transport = paramiko.Transport(client_socket)
        ssh_server = SSHServer()
        transport.add_server_key(self.server_key)
        try:
            transport.start_server(server=ssh_server)
        except paramiko.SSHException:
            return

        channel = transport.accept(20)
        if channel is None:
            print("No channel.")
            return
        # Use a lock to prevent multiple players from deciding they are player 1
        with self.channel_lock:
            self.connections.append(channel)
            player = len(self.connections) + 1

        print("Authenticated!")
        channel.send("\r\n")
        channel_file = channel.makefile()

        try:
            while len(self.connections) < 2:
                channel.sendall("\x1b[H\x1b[J")
                channel.sendall(self.waiting_message)
                time.sleep(0.5)
            while True:
                # Clear screen
                channel.sendall("\x1b[H\x1b[J")
                time.sleep(0.5)
        except Exception as e:
            print(f"Exception: {e}")

        finally:
            if client in self.connections:
                self.connections.remove(client)
            channel.close()
