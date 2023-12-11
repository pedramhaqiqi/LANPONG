# LANPONG Documentation for Project Report

## Overview

This documents describes LANPONG - a simple pong game SSH server.

The project features:
 - Public key authentication, and user registration
 - Multiple simultaneous games
 - User network statistics, such as latency
 - A database to store user statistics and lifetime scores

### Notes:

In any of the following examples `[...]` indicates omitted code for brevity.

## The server

The server object itself is located in `server.py`:

```python
class Server:
    def __init__(self, key_file_name="test_key") -> None:
        self.lock = threading.Lock()
        self.db = DB()
        self.server_key = paramiko.RSAKey.from_private_key_file(filename=key_file_name)
        # Set of usernames of connected clients.
        # Used to prevent multiple connections from the same user.
        self.connections = set()
```

We provide a default key file, `test_key`, which requires no password. It exists for ease of use.

To improve security, we recommend generating a new RSA key file and setting a password.

However, please note this will require all connecting clients to have the new key file.

<div style="page-break-after: always;"></div>

This server is initialized and started in `main.py` as follows:

```python
def main():
    server = Server()
    server.start_server()
```

Once the server is running, it will listen for incoming connections on port 22 (SSH):

```python
def start_server(self, host="0.0.0.0", port=2222):
    [...]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        # Bind socket to port and start listening for connections.
        [...]
        print(f"Listening for connection on {host}:{port}")

        # Accept multiple connections, thread-out
        while True:
            [...]
            print(f"Incoming connection from {client_addr[0]}:{client_addr[1]}")
            client_thread = threading.Thread(
                target=self.handle_client, args=(client_socket,)
            )
            client_thread.start()
```

Once a client connects, the server will start a new thread to handle the connection (`handle_client`):

```python
def handle_client(self, client_socket):
    [...]
    try:
        # Initialize the SSH server protocol for this connection.
        transport = paramiko.Transport(client_socket)
        ssh_server = SSHClientHandler(self)
        transport.add_server_key(self.server_key)
        transport.start_server(server=ssh_server)
        [...]
```

<div style="page-break-after: always;"></div>

The `SSHClientHandler` is a helper class that handles the SSH connection with the client.

In this class, we check if the connecting user exists (is in the database) and is not already connected:

```python
def get_allowed_auths(self, username):
    [...]
    with self.lock:
        if (not username == "new") and (username in self.connections):
            return "none"

        user = self.db.get_user(username)
        allowed = ["password"]
        if user is None:
            return "none"
        elif user.get("public_key") is not None:
            allowed.append("publickey")
        return ",".join(allowed)

```

This will let us know if the user is allowed to connect, and if so, how they are allowed to authenticate.

## User Authentication

Returning to `Server.handle_client` in `server.py`, if the user connected via `ssh new@<server_ip>`, we will register them:

```python
[...]
# If username is new prompt to register.
if user["username"] == "new":
    register_account()
    return
```

`register_account` will prompt the user for a username and password, and add them to the database.
See the `register_account` function in `server.py` for more details.

If the user connected via `ssh <username>@<server_ip>`, and the username exists in the database, we will prompt them for a password.

<div style="page-break-after: always;"></div>

Once, authenticated, the user will see the lobby screen:

```py
+-------------------------------------------------------------------------------------+
+                     _       ___   _   _ ______ _____ _   _ _____                    +
+                    | |     / _ \ | \ | || ___ \  _  | \ | |  __ \                   +
+                    | |    / /_\ \|  \| || |_/ / | | |  \| | |  \/                   +
+                    | |    |  _  || . ` ||  __/| | | | . ` | | __                    +
+                    | |____| | | || |\  || |   \ \_/ / |\  | |_\ \                   +
+                    \_____/\_| |_/\_| \_/\_|    \___/\_| \_/\____/                   +
+                                                                                     +
+                             Welcome to LAN PONG, mark!                              +
+                                    Leaderboard:                                     +
+                                  1. jane_doe - 150                                  +
+                                  2. john_doe - 120                                  +
+                                     3. mark - 9                                     +
+                                     4. sam - 4                                      +
+                                     5. new - 0                                      +
+                                  6. joeevans - 0                                    +
+                                                                                     +
+                                Press key to proceed:                                +
+                                   [1] Matchmaking                                   +
+                            [2] Public key configuration                             +
+                                                                                     +
+                                                                                     +
+                                                                                     +
+                                                                                     +
+                                                                                     +
+                                                                                     +
+                                                                                     +
+                                                                                     +
+                                                                                     +
+                                                                                     +
+                                                                                     +
+                                                                                     +
+                                                                                     +
+                                                                                     +
+                                                                                     +
+-------------------------------------------------------------------------------------+
+                                                                                     +
+                                                                                     +
+                                                                                     +
+                                                                                     +
+-------------------------------------------------------------------------------------+

```
<div style="page-break-after: always;"></div>

## Public Key Authentication

If the user selects option 2, they will be prompted to add a public key:

```python
def add_public_key():
    [...]
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
```

The user will be prompted to paste their public key, which will be added to the database.
This key will then be used for future authentication.

## Matchmaking

If the user selects option 1, they will be placed in an available game, or a new game will be created:

```python
[...]
game, player_id = self.get_game_or_create(user["username"])
[...]
```

`get_game_or_create` will return an available game, or create a new game if none are available.
If a new game is created, a new thread will be started to handle the game:

```python
def get_game_or_create(self, username):
    with self.games_lock:
           [...]
           game_thread = threading.Thread(target=self.handle_game, args=(game,))
           game_thread.start()
           [...]
```
<div style="page-break-after: always;"></div>

## The Game

Once two players are connected to a game, the game will start:

```python
[...]
input_thread = threading.Thread(target=handle_input, args=(player_id, game))
input_thread.start()
[...]
```
This will create a thread to listen for all keystrokes received from the client.
For the purpose of this documentation (and course-relevance) we will not go into detail regarding the game logic.

Another thread will be created to measure the latency to the client:

```python
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
```
<div style="page-break-after: always;"></div>

### Ping

The ping thread will send a ping request to the client every 50ms:

```python
def handle_ping(self, game: Game, ping: Ping, name, player_id):
    [...]
    game.is_game_started_event.wait()
    while game.loser == 0:
        game.update_network_stats(f"{name}'s PING: {ping.get():.3F}ms", player_id)
        time.sleep(0.05)
```

`game.update_network_stats` will update the network statistics and allow live viewing of the latency during gameplay:

```cpp
[...](Game TUI Above)
+---------------------------------------------------------------------------------------+
+                                  Network Statistics                                   +
+sam's PING: 0.095ms                                                mark's PING: 0.112ms+
+                                                                                       +
+                                                                                       +
+---------------------------------------------------------------------------------------+
```
<div style="page-break-after: always;"></div>

## Database

Lastly, we will briefly discuss the database.
The database is a simple class that uses a JSON file to store user data:

```python
def load_db(self):
    [...]
    with open(self.path, "r") as file:
        return json.load(file)
```

(Similarly, on save:)

```python
def save_db(self):
    [...]
    with open(self.path, "w") as file:
        json.dump(self.users, file, indent=2)
```

The database stores (non-sensitive) user data, such as username, public key, and lifetime score:

```json
[...]
  {
    "id": 6,
    "username": "sam",
    "password": "123",
    "score": 4,
    "public_key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMjlXfHr4jxk5g76UG0mlbI/oosXnD94MrYle/39+b+2 markchen8717@gmail.com",
    "key_type": "ed25519"
  }
[...]
```

This allows us to persist user data between server restarts.

## Conclusion

This concludes the documentation for the LANPONG server.

Please see our project report for an account of the development process.

For more information, please see the source code, or contact the authors.


