import socket
import threading

import paramiko

RSA_KEY = paramiko.RSAKey.from_private_key_file("test_key")


# Global list to keep track of all client connections
client_connections = []


def broadcast_message(message, sender):
    for client in client_connections:
        if client != sender:
            client.sendall(message.encode())


class SSHServer(paramiko.ServerInterface):
    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_pty_request(
        self, channel, term, width, height, pixelwidth, pixelheight, modes
    ):
        # Investigate whether useful for draw
        return True

    def check_channel_shell_request(self, channel):
        return True

    def check_auth_password(self, username, password):
        # QoL change/Need db for secure auth
        # if (username == "admin") and (password == "password"):
        #     print("Password accepted")
        #     return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_SUCCESSFUL


def handle_client(client):
    transport = paramiko.Transport(client)
    server_key = RSA_KEY
    transport.add_server_key(server_key)
    ssh_server = SSHServer()
    transport.start_server(server=ssh_server)

    # Add client to the global list
    client_connections.append(client)

    # Assuming you have a channel to receive data from the client
    channel = transport.accept()
    while True:
        data = channel.recv(1024)
        if not data:
            break
        message = f"Message from {client.getpeername()}: {data.decode()}"
        print(message)
        # broadcast_message(message, client)


def start_server(host="0.0.0.0", port=2222):
    """Starts an SSH server on specified port and address

    Args:
        host (str): Server host addr. Defaults to '0.0.0.0'.
        port (int): Port. Defaults to 2222.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(100)
    print(f"Listening for connection on {host}:{port}")

    while True:
        # TCP Socket initialization
        client_socket, client_addr = sock.accept()
        print(f"Incoming connection from {client_addr[0]}:{client_addr[1]}")
        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()


start_server()
