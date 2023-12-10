import paramiko
import lanpong.server.db as db
from io import StringIO
import base64


class SSHServer(paramiko.ServerInterface):
    def __init__(self, server):
        self.db = server.db
        self.user = None
        self.lock = server.lock
        self.connections = server.connections

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
        self.user = self.db.login(username, password)
        if self.user:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        user = self.db.get_user(username)
        key_gen_func = {"ed25519": paramiko.ed25519key.Ed25519Key}

        pbk = user["public_key"].split(" ", 3)
        user_key = key_gen_func[user["key_type"]](data=base64.b64decode(pbk[1]))
        if key == user_key:
            self.user = user
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        with self.lock:
            if username in self.connections:
                return "none"

            user = self.db.get_user(username)
            allowed = ["password"]
            if user is None:
                return "none"
            elif user["public_key"] is not None:
                allowed.append("publickey")
            return ",".join(allowed)

    def get_banner(self):
        return ("LAN PONG\r\n", "en-US")
