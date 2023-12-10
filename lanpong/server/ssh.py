import paramiko
import lanpong.server.db as db


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

    def get_banner(self):
        return ("My SSH Server\r\n", "en-US")
