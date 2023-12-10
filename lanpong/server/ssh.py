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
        print(username, password)
        return paramiko.AUTH_SUCCESSFUL

    def get_banner(self):
        return ("My SSH Server\r\n", "en-US")
