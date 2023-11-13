import asyncio
import sys

import asyncssh


class SSHServer(asyncssh.SSHServer):
    def connection_made(self, conn):
        print("SSH connection received from %s." % conn.get_extra_info("peername")[0])

    def connection_lost(self, exc):
        if exc:
            print("SSH connection error: " + str(exc), file=sys.stderr)
        else:
            print("SSH connection closed.")


async def start_server():
    await asyncssh.create_server(
        SSHServer, "", 22, server_host_keys=["/Users/pedramhaqiqi/.ssh/key"]
    )


def run_server():
    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(start_server())
    except (OSError, asyncssh.Error) as exc:
        sys.exit("Error starting server: " + str(exc))
    loop.run_forever()
