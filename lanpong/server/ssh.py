import socket
import threading

import paramiko


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

    def get_banner(self):
        return ("My SSH Server\r\n", "en-US")


server_key = paramiko.RSAKey.from_private_key_file("test_key")


def handle_client(client):
    transport = paramiko.Transport(client)
    ssh_server = SSHServer()
    transport.add_server_key(server_key)
    try:
        transport.start_server(server=ssh_server)
    except paramiko.SSHException:
        return

    channel = transport.accept(20)
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
    except Exception as e:
        print(f"Exception: {e}")

    finally:
        channel.close()


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
