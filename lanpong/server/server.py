import re
import socket
import threading
import time
from itertools import count

import paramiko
import numpy as np

from ..game.game import Game
from lanpong.server.ssh import SSHServer
from lanpong.server.db import DB

CLEAR_SCREEN = "\x1b[H\x1b[J"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"

LOGO_ASCII = """\
 _       ___   _   _ ______ _____ _   _ _____
| |     / _ \ | \ | || ___ \  _  | \ | |  __ \\
| |    / /_\ \|  \| || |_/ / | | |  \| | |  \/
| |    |  _  || . ` ||  __/| | | | . ` | | __
| |____| | | || |\  || |   \ \_/ / |\  | |_\ \\
\_____/\_| |_/\_| \_/\_|    \___/\_| \_/\____/""".splitlines()


def get_message_screen(message):
    screen = Game.get_blank_screen()
    rows, cols = screen.shape
    assert len(message) < cols - 2

    start = (cols - len(message)) // 2
    screen[rows // 2, start : start + len(message)] = list(message)

    return Game.screen_to_tui(screen)


def send_frame(channel, frame):
    return channel.sendall("".join([CLEAR_SCREEN, frame, HIDE_CURSOR]))


def get_lobby_screen(db, username=""):
    screen = Game.get_blank_screen()
    rows, cols = screen.shape

    assert len(LOGO_ASCII[0]) < cols - 2
    for i, line in enumerate(LOGO_ASCII):
        screen[1 + i, 1 : len(line) + 1] = list(line)
    current_row = 1 + len(LOGO_ASCII) + 1

    for i, line in enumerate(
        [f"Welcome to LAN PONG, {username}!", "Leaderboard:"]
        + [
            f"{i + 1}. {user['username']} - {user['score']}"
            for i, user in enumerate(db.get_top_users(10))
        ]
        + ["1. Matchmaking", "2. Public key configuration"]
    ):
        screen[current_row + i, 1 : len(line) + 1] = list(line)

    return Game.screen_to_tui(screen)


def wait_for_char(channel_file, valid_chars):
    while True:
        char = channel_file.read(1).decode()
        if char in valid_chars:
            return char


class Server:
    def __init__(self, key_file_name="test_key") -> None:
        self.db = DB()
        self.server_key = paramiko.RSAKey.from_private_key_file(filename=key_file_name)
        self.connections = []
        self.waiting_screen = get_message_screen(
            f"You are player 1. Waiting for player 2..."
        )
        self.games = []
        self.games_lock = threading.Lock()

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

    def handle_game(self, game: Game):
        """
        Handles the non-paddle game updates (mainly the ball)
        """
        game.is_game_started_event.wait()
        while game.loser == 0:
            game.update_ball()
            time.sleep(0.05)

    def echo_line(self, channel_file, channel):
        line = ""

        while True:
            char = channel_file.read(1).decode()

            # Handle backspace (ASCII 8 or '\b' or '\x7F')
            if char in {"\x08", "\b", "\x7F"}:
                if line:
                    # Remove the last character from the line and move the cursor back
                    line = line[:-1]
            elif char == "\r" or char == "\n":
                break
            else:
                line += char
                channel.sendall(char)
        return line

    def get_game_or_create(self):
        """
        Returns a game that is not full, or creates a new one
        Returns:
            (Game, int): Game and player id
        """
        with self.games_lock:
            game = next((g for g in self.games if not g.is_full()), None)
            if game is None:
                # No game available, create a new one
                game = Game()
                self.games.append(game)
                # Initialize client
                game_thread = threading.Thread(target=self.handle_game, args=(game,))
                game_thread.start()
            player_id = game.initialize_player()
            return game, player_id

    def handle_client(self, client_socket):
        try:
            transport = paramiko.Transport(client_socket)
            ssh_server = SSHServer()
            transport.add_server_key(self.server_key)
            transport.start_server(server=ssh_server)
            channel = transport.accept(20)
            if channel is None:
                raise ValueError("No channel")
            user = ssh_server.user
            channel.send("\r\n")
            channel_file = channel.makefile()

            def register_account():
                for i in count():
                    message = (
                        "Welcome to LAN PONG!\r\n"
                        "Please create an account.\r\n"
                        "Enter your desired username: "
                        if i == 0
                        else "Username either already exists or contains invalid characters( No white spaces or empty string).\r\n"
                        "Please enter another username: "
                    )
                    send_frame(channel, message)
                    username = self.echo_line(channel_file, channel)
                    if self.db.is_username_valid(username):
                        break

                send_frame(channel, "Enter your password:")
                password = self.echo_line(channel_file, channel)

                self.db.create_user(username, password)
                send_frame(
                    channel,
                    "Account registered successfully. Please login with your credentials.\r\n",
                )

            def add_public_key():
                key_types = {"1": "ed25519"}
                send_frame(channel, "Please select a key type:\r\n1. Ed25519\r\n")
                choice = wait_for_char(channel_file, set(key_types.keys()))

                key_type = key_types[choice]
                send_frame(channel, f"Please paste your {key_type} public key (entire content):\r\n")
                public_key = self.echo_line(channel_file, channel)
                self.db.update_user(
                    user["id"], {"public_key": public_key, "key_type": key_type}
                )

            def handle_input(player_id, game):
                while True:
                    try:
                        key = channel_file.read(1) if channel.recv_ready() else b""
                    except Exception as e:
                        print(f"Exception: {e}")
                        break
                    game.update_paddle(player_id, key)
                    time.sleep(0.05)

            # If username is new prompt to register
            if user["username"] == "new":
                register_account()
                return

            # Show lobby and match making option screen
            send_frame(channel, get_lobby_screen(self.db, user["username"]))
            while (char := wait_for_char(channel_file, {"1", "2"})) == "2":
                add_public_key()
                send_frame(channel, get_lobby_screen(self.db, user["username"]))

            game, player_id = self.get_game_or_create()
            game.set_player_ready(player_id, True)

            # Show waiting screen until there are two players
            while not game.is_full():
                send_frame(channel, self.waiting_screen)
                time.sleep(0.5)

            input_thread = threading.Thread(target=handle_input, args=(player_id, game))
            input_thread.start()
            while game.loser == 0:
                send_frame(channel, str(game))
                time.sleep(0.05)
            # Game is over
            winner = 1 if game.loser == 2 else 2
            send_frame(channel, get_message_screen(f"Player {winner} wins!"))
        except Exception as e:
            print(f"Exception: {e}")
        finally:
            if channel is not None:
                channel.close()
            client_socket.close()
