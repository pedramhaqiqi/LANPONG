import paramiko
import lanpong.server.db as db
from io import StringIO
import base64


class SSHServer(paramiko.ServerInterface):
    def __init__(self, server):
        """
        Initialize the SSH server.

        Parameters:
        - server: Instance of the server containing a database, user information, lock, and connections.
        """
        self.db = server.db
        self.user = None
        self.lock = server.lock
        self.connections = server.connections

    def check_channel_request(self, kind, chanid):
        """
        Callback for checking if a channel request is allowed.

        Parameters:
        - kind: Type of channel request.
        - chanid: Channel ID.

        Returns:
        - paramiko.OPEN_SUCCEEDED if the request is allowed, else paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED.
        """
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_pty_request(
        self, channel, term, width, height, pixelwidth, pixelheight, modes
    ):
        """
        Callback for checking if a PTY request is allowed.

        Parameters:
        - channel: The channel requesting the PTY.
        - term: Terminal type.
        - width: Width of the terminal.
        - height: Height of the terminal.
        - pixelwidth: Width of the terminal in pixels.
        - pixelheight: Height of the terminal in pixels.
        - modes: Terminal modes.

        Returns:
        - True if the PTY request is allowed.
        """
        # Investigate whether useful for draw
        return True

    def check_channel_shell_request(self, channel):
        """
        Callback for checking if a shell request is allowed.

        Parameters:
        - channel: The channel requesting the shell.

        Returns:
        - True if the shell request is allowed.
        """
        return True

    def check_auth_password(self, username, password):
        """
        Callback for checking password-based authentication.

        Parameters:
        - username: Username attempting authentication.
        - password: Password provided for authentication.

        Returns:
        - paramiko.AUTH_SUCCESSFUL if authentication is successful, else paramiko.AUTH_FAILED.
        """
        try:
            self.user = self.db.login(username, password)
            if self.user:
                return paramiko.AUTH_SUCCESSFUL
            return paramiko.AUTH_FAILED
        except:
            return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        """
        Callback for checking public key-based authentication.

        Parameters:
        - username: Username attempting authentication.
        - key: Public key provided for authentication.

        Returns:
        - paramiko.AUTH_SUCCESSFUL if authentication is successful, else paramiko.AUTH_FAILED.
        """
        try:
            user = self.db.get_user(username)
            key_gen_func = {"ed25519": paramiko.ed25519key.Ed25519Key}

            pbk = user["public_key"].split(" ", 3)
            user_key = key_gen_func[user["key_type"]](data=base64.b64decode(pbk[1]))
            if key == user_key:
                self.user = user
                return paramiko.AUTH_SUCCESSFUL
            return paramiko.AUTH_FAILED
        except:
            return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        """
        Callback for getting allowed authentication methods for a user.

        Parameters:
        - username: Username for which allowed authentication methods are requested.

        Returns:
        - Comma-separated string of allowed authentication methods.
        """
        with self.lock:
            if username in self.connections:
                return "none"

            user = self.db.get_user(username)
            allowed = ["password"]
            if user is None:
                return "none"
            elif user.get("public_key") is not None:
                allowed.append("publickey")
            return ",".join(allowed)

    def get_banner(self):
        """
        Callback for getting a banner to send to clients during connection.

        Returns:
        - Tuple containing the banner text ("LAN PONG\r\n") and language code ("en-US").
        """
        return ("LAN PONG\r\n", "en-US")
