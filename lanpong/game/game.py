import numpy as np
from collections import namedtuple


Ball = namedtuple("Ball", ["coords", "velocity", "direction"])
Paddle = namedtuple("Paddle", ["coords", "height"])


def normalize(vec):
    return vec / np.linalg.norm(vec)


class Game:
    """
    Game object for pong
    """

    DEFAULT_HEIGHT = 24
    DEFAULT_WIDTH = 80
    DEFAULT_PADDLE_HEIGHT = 6

    def __init__(self):
        self.width = Game.DEFAULT_WIDTH
        self.height = Game.DEFAULT_HEIGHT
        # TODO: Other __init__ stuff
        self.board = np.chararray((self.height, self.width))
        self.ball = Ball(
            (self.height // 2, self.width // 2),
            1,
            normalize(np.random.uniform(-1, 1, 2)),
        )

        self.paddle1 = Paddle((1, self.height // 2), Game.DEFAULT_PADDLE_HEIGHT)
        self.paddle2 = Paddle(
            (self.width - 2, self.height // 2), Game.DEFAULT_PADDLE_HEIGHT
        )

    def update_ball(self):
        """Updates the ball position"""
        pass

    def update_paddle(self, player_number: int, key):
        """Updates the paddle positions"""
        pass

    def update(self):
        """Updates the game state"""
        pass

    def get_next_frame(self) -> str:
        """
        Returns the current game state as a single string representing the board when printed to stdout
        Uses: update() method
        """
        self.update()
        # TODO: Return game state as string

        pass
