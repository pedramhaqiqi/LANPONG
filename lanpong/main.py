"""
- Import things from your .base module
"""
import time
from lanpong.server.server import Server
from lanpong.game.game import Game


def main():
    server = Server()
    server.start_server()
