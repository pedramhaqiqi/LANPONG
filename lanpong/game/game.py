import numpy as np
from collections import namedtuple


Ball = namedtuple("Ball", ["coords", "velocity", "direction"])


def normalize(vec):
    return vec / np.linalg.norm(vec)


class Paddle:
    """
    Paddle object for pong
    """

    def __init__(self, height, column):
        self.height = height
        self.column = column


class Player:
    """
    Player object for pong
    """

    def __init__(self, paddle):
        self.is_initialized = False
        self.paddle = paddle


class Game:
    """
    Game object for pong
    """

    DEFAULT_HEIGHT = 24
    DEFAULT_WIDTH = 80
    DEFAULT_PADDLE_HEIGHT = DEFAULT_HEIGHT // 2

    def __init__(self):
        self.width = Game.DEFAULT_WIDTH
        self.height = Game.DEFAULT_HEIGHT
        self.board = np.zeros((self.height, self.width), dtype="U1")
        self.started = False

        # Draw the board
        for i in range(self.height):
            for j in range(self.width):
                if i == 0 or i == self.height - 1:
                    self.board[i][j] = "-"
                elif j == 0 or j == self.width - 1:
                    self.board[i][j] = "|"
                else:
                    self.board[i][j] = " "

        # TODO: Ball
        self.ball = Ball(
            (self.height // 2, self.width // 2),
            1,
            normalize(np.random.uniform(-1, 1, 2)),
        )

        self.paddle1 = Paddle(self.height // 2, 1)
        self.paddle2 = Paddle(self.height // 2, self.width - 2)

        # Draw the paddles
        self.board[self.paddle1.height][self.paddle1.column] = "|"
        self.board[self.paddle2.height][self.paddle2.column] = "|"

        self.player1 = Player(self.paddle1)
        self.player2 = Player(self.paddle2)

    def initialize_player(self):
        """Initializes a player. Returns non-zero player id, 0 if game is full."""
        if not self.player1.is_initialized:
            self.player1.is_initialized = True
            return 1
        elif not self.player2.is_initialized:
            self.player2.is_initialized = True
            return 2
        else:
            return 0

    def update_ball(self):
        """Updates the ball position"""
        pass

    def update_paddle(self, player_number: int, key):
        """Updates the paddle positions"""
        player = self.player1 if player_number == 1 else self.player2
        paddle = player.paddle
        old_height = player.paddle.height
        new_height = old_height

        # Only update paddle position if the key is valid and the paddle is not at the edge of the board
        if key == "w" and old_height > 1:
            new_height = old_height - 1
        elif key == "s" and old_height < self.height - 2:
            new_height = old_height + 1

        # Clear old paddle
        self.board[old_height][paddle.column] = " "
        # Draw new paddle
        self.board[new_height][paddle.column] = "|"
        # Update new paddle position
        paddle.height = new_height

    def get_board(self) -> str:
        """
        Returns the current game state as a single string representing the board when printed to stdout
        Uses: update() method
        """
        # TODO: Return game state as string
        state = ""
        for i in range(self.height):
            for j in range(self.width):
                print(self.board[i][j])
                state += self.board[i][j]
            state += "\n"
        return state
