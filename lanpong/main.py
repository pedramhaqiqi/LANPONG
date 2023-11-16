"""
- Import things from your .base module
"""
from lanpong.server.server import Server


def main():  # pragma: no cover
    server = Server()
    server.start_server()
