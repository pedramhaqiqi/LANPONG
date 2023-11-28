"""
- Import things from your .base module
"""
from lanpong.server.server import Server
from lanpong.game.game import Game


def main():  # pragma: no cover
    # server = Server()
    # server.start_server()

    # write infinite loop to ask for player1 and player2 input and update and print the board
    game = Game()
    game.initialize_player()
    game.initialize_player()
    while True:
        user1_input = input("User1 Enter something: ")
        user2_input = input("User2 Enter something: ")
        game.update_paddle(1, user1_input)
        game.update_paddle(2, user2_input)
        print(game.get_board())
