import re
import socket
import threading
import time
from itertools import count
import paramiko
import numpy as np
from ..game.game import Game
from lanpong.server.ssh import SSHServer
from lanpong.server.ping import Ping
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
    """
    Returns a screen with the message centered.
    """
    screen = Game.get_blank_screen(stats_height=0)
    rows, cols = screen.shape
    assert len(message) < cols - 2

    start = (cols - len(message)) // 2
    screen[rows // 2, start : start + len(message)] = list(message)

    return Game.screen_to_tui(screen)


def send_frame(channel, frame):
    """
    Sends a frame to the client.
    """
    return channel.sendall("".join([CLEAR_SCREEN, frame, HIDE_CURSOR]))


def get_lobby_screen(db, username=""):
    """
    Returns the lobby screen with the leaderboard and options.
    """
    screen = Game.get_blank_screen()
    rows, cols = screen.shape

    assert len(LOGO_ASCII[0]) < cols - 2
    start = (cols - len(LOGO_ASCII[0])) // 2
    for i, line in enumerate(LOGO_ASCII):
        # Center each line of the logo.
        screen[1 + i, start : start + len(line)] = list(line)
    current_row = 1 + len(LOGO_ASCII) + 1

    for i, line in enumerate(
        [f"Welcome to LAN PONG, {username}!", "Leaderboard:"]
        + [
            f"{i + 1}. {user['username']} - {user['score']}"
            for i, user in enumerate(db.get_top_users(10))
        ]
        + [
            "",
            "Press key to proceed:",
            "[1] Matchmaking",
            "[2] Public key configuration",
        ]
    ):
        # Center each line.
        start = (cols - len(line)) // 2
        screen[current_row + i, start : len(line) + start] = list(line)

    return Game.screen_to_tui(screen)


def wait_for_char(channel_file, valid_chars):
    """
    Waits for a character from the client that is in the valid_chars set.
    """
    while True:
        char = channel_file.read(1).decode()
        if char in valid_chars:
            return char


class Server:
    def __init__(self, key_file_name="test_key") -> None:
        self.lock = threading.Lock()
        self.db = DB()
        self.server_key = paramiko.RSAKey.from_private_key_file(filename=key_file_name)
        self.connections = set()
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
            # Bind socket to port and start listening for connections.
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
            game.update_game()
            time.sleep(0.05)

    def handle_ping(self, game: Game, ping: Ping, name, player_id):
        """
        Handles the ping updates
        """
        game.is_game_started_event.wait()
        while game.loser == 0:
            game.update_network_stats(f"{name}'s PING: {ping.get():.3F}ms", player_id)
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

    def get_game_or_create(self, username):
        """
        Returns a game that is not full, or creates a new one
        Returns:
            (Game, int): Game and player id
        """
        with self.games_lock:
            # Get a game that is not full, or None if all games are full.
            game = next((g for g in self.games if not g.is_full()), None)
            if game is None:
                # No game available, create a new one.
                game = Game()
                self.games.append(game)
                # Create a thread for this game and start it.
                game_thread = threading.Thread(target=self.handle_game, args=(game,))
                game_thread.start()
            player_id = game.initialize_player(username)
            return game, player_id

    def handle_client(self, client_socket):
        try:
            # Initialize the SSH server protocol for this connection.
            transport = paramiko.Transport(client_socket)
            ssh_server = SSHServer(self)
            transport.add_server_key(self.server_key)
            transport.start_server(server=ssh_server)
            channel = transport.accept(20)
            if channel is None:
                raise ValueError("No channel")

            user = ssh_server.user
            with self.lock:
                self.connections.add(user["username"])

            channel_file = channel.makefile()

            # Helper functions for handling keystokes and registration:
            def register_account():
                for i in count():
                    # Repeat until have a valid username.
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

                # Get password (empty is ok).
                send_frame(channel, "Enter your password (empty for no password):")
                password = self.echo_line(channel_file, channel)

                # Add newly registered user to the database.
                self.db.create_user(username, password)
                send_frame(
                    channel,
                    "Account registered successfully. Please login with your credentials.\r\n",
                )

            def add_public_key():
                # Only support ed25519.
                key_types = {"1": "ed25519"}
                send_frame(channel, "Please select a key type:\r\n1. Ed25519\r\n")
                choice = wait_for_char(channel_file, set(key_types.keys()))

                key_type = key_types[choice]
                send_frame(
                    channel,
                    f"Please paste your {key_type} public key (entire content):\r\n",
                )
                # Receive the public key and add it to the database.
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
                    # Update the paddles location based on the key pressed.
                    game.update_paddle(player_id, key)
                    time.sleep(0.05)

            # If username is new prompt to register.
            if user["username"] == "new":
                register_account()
                return

            # Show lobby and match making option screen.
            send_frame(channel, get_lobby_screen(self.db, user["username"]))
            while (char := wait_for_char(channel_file, {"1", "2"})) == "2":
                add_public_key()
                send_frame(channel, get_lobby_screen(self.db, user["username"]))

            game, player_id = self.get_game_or_create(user["username"])
            game.set_player_ready(player_id, True)

            # Show waiting screen until there are two players.
            while not game.is_full():
                send_frame(channel, self.waiting_screen)
                time.sleep(0.5)

            # Start thread to read ping (response time).
            input_thread = threading.Thread(target=handle_input, args=(player_id, game))
            input_thread.start()
            ping_thread = threading.Thread(
                target=self.handle_ping,
                args=(
                    game,
                    Ping(channel.getpeername()[0]),
                    user["username"],
                    player_id,
                ),
            )
            ping_thread.start()

            # Send the current TUI representation of the game state.
            while game.loser == 0:
                send_frame(channel, str(game))
                time.sleep(0.05)
            # Game is over
            winner_id = 1 if game.loser == 2 else 2
            winner = game.player1 if winner_id == 1 else game.player2

            if player_id == winner_id:
                self.db.update_user(user["id"], {"score": user["score"] + 1})

            send_frame(channel, get_message_screen(f"{winner.username} wins!"))
            time.sleep(2)
        except Exception as e:
            print(f"Exception: {e}")
        finally:
            # Clean up.
            if channel is not None:
                self.connections.remove(user["username"])
                send_frame(channel, SHOW_CURSOR)
            transport.close()
            client_socket.close()
