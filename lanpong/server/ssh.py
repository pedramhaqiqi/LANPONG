import paramiko
import lanpong.server.db as db
from io import StringIO
import base64


class SSHServer(paramiko.ServerInterface):
    def __init__(self):
        self.db = db.DB()
        self.user = None

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
        # Check if the provided public key is in the list associated with the username
        print(username, key)

        pbk = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMjlXfHr4jxk5g76UG0mlbI/oosXnD94MrYle/39+b+2 markchen8717@gmail.com".split(
            " ", 3
        )
        # not_really_a_file = StringIO(pbk)
        # mykey = paramiko.rsakey.RSAKey(file_obj=not_really_a_file)
        mykey = paramiko.ed25519key.Ed25519Key(data=base64.b64decode(pbk[1]))
        print(mykey)

        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return "password,publickey"

    def get_banner(self):
        return ("LAN PONG\r\n", "en-US")
