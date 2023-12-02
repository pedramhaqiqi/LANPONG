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
                new_game = None
                player_id = None
                # Find a game that is not full, otherwise create a new game
                with self.games_lock:
                    print(self.games)
                    for game in self.games:
                        with game.lock:
                            if not game.is_full():
                                new_game = game
                                player_id = new_game.initialize_player()
                                break
                    if new_game is None:
                        new_game = Game()
                        # initialize client
                        player_id = new_game.initialize_player()
                        game_thread = threading.Thread(
                            target=self.handle_game, args=(new_game,)
                        )
                        game_thread.start()
                        self.games.append(new_game)
                print("player id")
                print(player_id)
                print("Game started:")
                print(new_game.is_full())
                print(f"Incoming connection from {client_addr[0]}:{client_addr[1]}")
                client_thread = threading.Thread(
                    target=self.handle_client, args=(client_socket, new_game, player_id)
                )
                client_thread.start()

    def handle_game(self, game: Game):
        game.thread = threading.current_thread()
        while True:
            if game.is_full():
                game.started = True
                if game.started:
                    end_round = game.update_ball()
                    # if end_round:
                    #     current_thread = threading.current_thread()
                    #     current_thread.stop()
                    time.sleep(0.05)

    def handle_client(self, client_socket, game: Game, player_id):
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
        channel.send("\r\n")
        channel_file = channel.makefile()

        def handle_input(player_id, game):
            while True:
                try:
                    key = channel_file.read(1).decode()
                    game.update_paddle(player_id, key)
                except Exception as e:
                    print(f"Exception: {e}")
                    break

        try:
            # Show waiting screen until there are two players
            while game.started is False:
                channel.sendall("\x1b[H\x1b[J")
                channel.sendall(self.waiting_message)
                time.sleep(0.5)

            input_thread = threading.Thread(target=handle_input, args=(player_id, game))
            input_thread.start()
            while True:
                # Clear screen
                #   Check at start of loop if a player disconnect, disconnect both
                channel.sendall("\x1b[H\x1b[J")
                channel.sendall(str(game))
                time.sleep(0.05)
        except Exception as e:
            print(f"Exception: {e}")

        finally:
            if client in self.connections:
                self.connections.remove(client)
            channel.close()
