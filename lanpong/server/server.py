import socket
import threading

import paramiko

from lanpong.server.ssh import SSHServer


class Server:
    def broadcast_message(self, message, sender):
        for client in self.connections:
            if client != sender:
                try:
                    client.send(f"Message from {sender.getpeername()}: {message}\r\n")
                except socket.error as e:
                    print(f"Error sending message: {e}\r\n")
                    client.close()
                    self.connections.remove(client)

    def handle_client(self, client):
        transport = paramiko.Transport(client)
        ssh_server = SSHServer()
        transport.add_server_key(self.server_key)
        try:
            transport.start_server(server=ssh_server)
        except paramiko.SSHException:
            return

        channel = transport.accept(20)
        self.connections.append(channel)

        if channel is None:
            print("No channel.")
            return

        print("Authenticated!")
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
                print(f"Received data: {data_str} from {client.getpeername()}")

                # Optionally, send data back to the client
                channel.send(f"You typed: {data_str}\r\n")
                self.broadcast_message(data_str, channel)
        except Exception as e:
            print(f"Exception: {e}")

        finally:
            self.connections.remove(client)
            channel.close()

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

    def __init__(self, key_file_name="test_key") -> None:
        self.server_key = paramiko.RSAKey.from_private_key_file(filename=key_file_name)
        self.connections = []
