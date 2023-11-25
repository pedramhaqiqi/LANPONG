"""
- Import things from your .base module
"""
import sys
import threading

from lanpong.screens.start_screen import StartScreen
from lanpong.server.server import Server


def main():  # pragma: no cover
    server = Server()
    # start_screen = StartScreen()
    # start_screen.draw()
    # sys.stdout = start_screen.stdscreen
    server_thread = threading.Thread(target=server.start_server, args=())
    # server_broadcast_thread = threading.Thread(target=server.broadcast_from_server, args=("HELLO FROM SERVER\r\n",))
    # server_broadcast_thread.start()
    server_thread.start()
