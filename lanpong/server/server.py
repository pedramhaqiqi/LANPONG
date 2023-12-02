import socket
import threading
import time
import paramiko
import numpy as np

from ..game.game import Game
from lanpong.server.ssh import SSHServer


def get_message_screen(message):
    screen = Game.get_blank_screen()
    rows, cols = screen.shape
    assert len(message) < cols - 2

    start = (cols - len(message)) // 2
    screen[rows // 2, start : start + len(message)] = list(message)

    return Game.screen_to_tui(screen)


class Server:
    def __init__(self, key_file_name="test_key") -> None:
        self.server_key = paramiko.RSAKey.from_private_key_file(filename=key_file_name)
        self.connections = []
        self.waiting_message = get_message_screen(
            "You are player 1. Waiting for player 2..."
        )
        self.game = Game()

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
            game_thread = threading.Thread(target=self.handle_game, args=())
            game_thread.start()
            print(f"Listening for connection on {host}:{port}")

            # Accept multiple connections, thread-out
            while True:
                client_socket, client_addr = server_sock.accept()
                print(f"Incoming connection from {client_addr[0]}:{client_addr[1]}")
                client_thread = threading.Thread(
                    target=self.handle_client, args=(client_socket,)
                )
                client_thread.start()

    def handle_game(self):
        while True:
            if self.game.started:
                self.game.update_ball()
                time.sleep(0.05)

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
        self.connections.append(channel)

        print("Authenticated!")
        channel.send("\r\n")
        channel_file = channel.makefile()

        def handle_input(player_id):
            while True:
                try:
                    key = channel_file.read(1).decode()
                    self.game.update_paddle(player_id, key)
                except Exception as e:
                    print(f"Exception: {e}")
                    break

        try:
            player_id = self.game.initialize_player()
            # Show waiting screen until there are two players
            while player_id == 1 and len(self.connections) < 2:
                channel.sendall("\x1b[H\x1b[J")
                channel.sendall(self.waiting_message)
                time.sleep(0.5)
            self.game.started = True
            input_thread = threading.Thread(target=handle_input, args=(player_id,))
            input_thread.start()
            while True:
                # Clear screen
                channel.sendall("\x1b[H\x1b[J")
                channel.sendall(str(self.game))
                time.sleep(0.05)
        except Exception as e:
            print(f"Exception: {e}")

        finally:
            if client in self.connections:
                self.connections.remove(client)
            channel.close()
