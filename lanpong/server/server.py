import socket
import threading
import time
import paramiko
import numpy as np

from ..game.game import Game
from lanpong.server.ssh import SSHServer
from lanpong.server.ping import Ping


CLEAR_SCREEN = "\x1b[H\x1b[J"
HIDE_CURSOR = "\033[?25l"


def get_message_screen(message):
    screen = Game.get_blank_screen(stats_height=0)
    rows, cols = screen.shape
    assert len(message) < cols - 2

    start = (cols - len(message)) // 2
    screen[rows // 2, start : start + len(message)] = list(message)

    return Game.screen_to_tui(screen)


def send_frame(channel, frame):
    return channel.send("".join([CLEAR_SCREEN, frame, HIDE_CURSOR]))


class Server:
    def __init__(self, key_file_name="test_key") -> None:
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
                with self.games_lock:
                    new_game = next(
                        (game for game in self.games if not game.is_full()), None
                    )
                    if new_game is None:
                        # No game available, create a new one
                        new_game = Game()
                        self.games.append(new_game)
                        # Initialize client
                        game_thread = threading.Thread(
                            target=self.handle_game, args=(new_game,)
                        )
                        game_thread.start()
                player_id = new_game.initialize_player()
                print(f"player id: {player_id}, game started?: {new_game.is_full()}")
                client_thread = threading.Thread(
                    target=self.handle_client, args=(client_socket, new_game, player_id)
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

    def handle_ping(self, game: Game, ping: Ping, player_id):
        """
        Handles the ping updates
        """
        game.is_game_started_event.wait()
        while game.loser == 0:
            game.update_network_stats(
                f"PING: Player {player_id} {ping.get()}ms", player_id
            )
            time.sleep(0.05)

    def handle_client(self, client_socket, game: Game, player_id):
        def handle_input(player_id, game):
            while True:
                try:
                    key = channel_file.read(1) if channel.recv_ready() else b""
                except Exception as e:
                    print(f"Exception: {e}")
                    break
                game.update_paddle(player_id, key)
                time.sleep(0.05)

        transport = paramiko.Transport(client_socket)
        ssh_server = SSHServer()
        transport.add_server_key(self.server_key)
        try:
            transport.start_server(server=ssh_server)
        except paramiko.SSHException:
            return
        finally:
            # TODO: Clean up game
            pass

        channel = transport.accept(20)
        if channel is None:
            print("No channel.")
            # TODO: Clean up game
            return
        print("Authenticated!")
        game.set_player_ready(player_id, True)
        channel.send("\r\n")
        channel_file = channel.makefile()

        try:
            # Show waiting screen until there are two players
            while not game.is_full():
                send_frame(channel, self.waiting_screen)
                time.sleep(0.5)

            input_thread = threading.Thread(target=handle_input, args=(player_id, game))
            input_thread.start()

            ping_thread = threading.Thread(
                target=self.handle_ping,
                args=(game, Ping(channel.getpeername()[0]), player_id),
            )
            ping_thread.start()

            while game.loser == 0:
                send_frame(channel, str(game))
                time.sleep(0.05)
            # Game is over
            winner = 1 if game.loser == 2 else 2
            send_frame(channel, get_message_screen(f"Player {winner} wins!"))
        except Exception as e:
            print(f"Exception: {e}")
            if client in self.connections:
                self.connections.remove(client)
        finally:
            channel.close()
            client_socket.close()
