import socket
import threading
import time

import paramiko

from lanpong.screens.start_screen import StartScreen
from lanpong.server.ssh import SSHServer


class Server:
    def broadcast_from_server(self, message):
        while True:
            time.sleep(3)
            for client in self._connections:
                try:
                    client.send(message)
                except socket.error as e:
                    print(f"Error sending message: {e}\r\n")
                    client.close()
                    self._connections.remove(client)

    def broadcast_from_sender(self, message, sender):
        if not len(self._connections):
            return

        for client in self._connections:
            if client != sender:
                try:
                    client.send(f"message: {message} from {sender.getpeername()}\r\n")
                except socket.error as e:
                    print(f"Error sending message: {e}\r\n")
                    client.close()
                    self._connections.remove(client)

    def handle_client(self, client, start_screen: StartScreen = None):
        transport = paramiko.Transport(client)
        ssh_server = SSHServer()
        transport.add_server_key(self._server_key)
        try:
            transport.start_server(server=ssh_server)
        except paramiko.SSHException:
            return

        channel = transport.accept(20)
        self._connections.append(channel)

        if channel is None:
            print("No channel.")
            return

        print("Authenticated!\r")
        channel.send("content:" + start_screen.get_content())
        channel.send("\r\n")
        channel.send("Welcome to the SSH server. Type something:")
        channel.send("\r\n")

        try:
            while True:
                # Read data from client
                data = channel.recv(1024)
                if not data:
                    break

                # Convert to string and strip newlines
                data_str = data.decode("utf-8").strip()
                print(f"Received data: {data_str} from {client.getpeername()}\r")

                # Optionally, send data back to the client
                channel.send(f"You typed: {data_str}\r\n")
                self.broadcast_from_sender(data_str, channel)
        except Exception as e:
            print(f"Exception: {e}")

        finally:
            self.connections.remove(client)
            channel.close()

    def start_server(self, host="0.0.0.0", port=2222, start_screen: StartScreen = None):
        """Starts an SSH server on specified port and address

        Args:
            host (str): Server host addr. Defaults to '0.0.0.0'.
            port (int): Port. Defaults to 2222.
        """
        self.is_running.set()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((host, port))
            server_sock.listen(100)
            print(f"Listening for connection on {host}:{port}\r")

            # Accept multiple connections, thread-out
            while True:
                client_socket, client_addr = server_sock.accept()
                print(f"Incoming connection from {client_addr[0]}:{client_addr[1]}\r")
                client_thread = threading.Thread(
                    target=self.handle_client,
                    kwargs={
                        "client": client_socket,
                        "start_screen": start_screen,
                    },
                )
                client_thread.start()

    def __init__(self, key_file_name="test_key") -> None:
        self.is_running = threading.Event()
        self._server_key = paramiko.RSAKey.from_private_key_file(filename=key_file_name)
        self._connections = []
