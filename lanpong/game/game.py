import numpy as np
import threading

from itertools import chain
from collections import namedtuple


class Paddle:
    """
    Paddle object for pong
    """

    def __init__(self, height, column, length=2):
        self.height = height
        self.column = column
        self.length = length


class Player:
    """
    Player object for pong
    """

    def __init__(self, paddle):
        self.is_initialized = False
        self.paddle = paddle


class Ball:
    def __init__(self, coords, velocity_x, velocity_y):
        """
        Initialize the ball with its position and velocity components.
        :param x: The x-coordinate of the ball.
        :param y: The y-coordinate of the ball.
        :param velocity_x: The horizontal velocity component of the ball.
        :param velocity_y: The vertical velocity component of the ball.
        """
        self.coords = coords
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y

    def update_position(self):
        """
        Update the ball's position based on its velocity.
        """
        self.coords[0] += self.velocity_x
        self.coords[1] += self.velocity_y

    def invert_velocity_x(self):
        """
        Invert the horizontal velocity to simulate a bounce.
        """
        self.velocity_x *= -1

    def invert_velocity_y(self):
        """
        Invert the vertical velocity to simulate a bounce.
        """
        self.velocity_y *= -1

    def get_coords(self):
        return self.coords

    def get_x(self):
        return self.coords[0]

    def get_y(self):
        return self.coords[1]

    def check_wall_collision(self, width, height):
        if self.get_x() <= 0 or self.get_x() >= width - 1:
            return True
        if self.get_y() <= 0 or self.get_y() >= height - 1:
            self.invert_velocity_y()
            return False

    def check_paddle_collision(self, left_paddle, right_paddle):
        """
        Check if the ball has collided with a paddle.
        :param left/right_paddle: The paddle to check collision with.
        :return: True if the ball has collided with the paddle, False otherwise.
        """
        if (
            right_paddle.height == self.get_y()
            and right_paddle.column - 1 == self.get_x()
        ) or (
            left_paddle.height == self.get_y()
            and left_paddle.column + 1 == self.get_x()
        ):
            self.invert_velocity_x()

    def keep_within_bounds(self, width, height):
        self.coords[0] = np.clip(self.coords[0], 1, width - 2)
        self.coords[1] = np.clip(self.coords[1], 1, height - 2)


class Game:
    """
    Game object for pong
    """

    DEFAULT_HEIGHT = 24
    DEFAULT_WIDTH = 70
    DEFAULT_PADDLE_HEIGHT = DEFAULT_HEIGHT // 2

    def __init__(self):
        self.width = Game.DEFAULT_WIDTH
        self.height = Game.DEFAULT_HEIGHT
        self.started = False
        self.lock = threading.Lock()

        self.ball = Ball(
            [self.width // 2, self.height // 2],
            1,
            1,
        )

        self.paddle1 = Paddle(self.height // 2, 1)
        self.paddle2 = Paddle(self.height // 2, self.width - 2)

        self.screen = Game.get_blank_screen()
        # Draw the paddles
        self.screen[self.paddle1.height][self.paddle1.column] = "|"
        self.screen[self.paddle2.height][self.paddle2.column] = "|"
        # Draw the ball
        self.screen[self.ball.get_y()][self.ball.get_x()] = "*"

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
        old_coords = self.ball.get_coords().copy()

        self.ball.update_position()
        self.ball.check_paddle_collision(self.player1.paddle, self.player2.paddle)
        end_round = self.ball.check_wall_collision(self.width, self.height)
        if end_round:
            return True

        self.ball.keep_within_bounds(self.width, self.height)

        # Clear the old position of the ball
        self.screen[old_coords[1]][old_coords[0]] = " "

        # Draw the ball at its new position
        self.screen[self.ball.get_y()][self.ball.get_x()] = "*"

    def update_paddle(self, player_number: int, key):
        """Updates the paddle positions"""
        player = self.player1 if player_number == 1 else self.player2
        paddle = player.paddle
        old_height = player.paddle.height
        new_height = old_height

        # Only update paddle position if the key is valid and the paddle is not at the edge of the screen
        if key == "w" and old_height > 1:
            new_height = old_height - 1
        elif key == "s" and old_height < self.height - 2:
            new_height = old_height + 1

        # Clear old paddle
        self.screen[old_height][paddle.column] = " "
        # Draw new paddle
        self.screen[new_height][paddle.column] = "|"
        # Update new paddle position
        paddle.height = new_height

    def __str__(self):
        return Game.screen_to_tui(self.screen)

    # def (self, callback):

    def is_full(self):
        return (
            self.player1.is_initialized is True and self.player2.is_initialized is True
        )

    @staticmethod
    def get_blank_screen():
        """Return a blank screen with no paddles or ball, just the border"""
        screen = np.full((Game.DEFAULT_HEIGHT, Game.DEFAULT_WIDTH), " ", dtype="S1")
        screen[0, :] = screen[-1, :] = "-"
        screen[:, 0] = screen[:, -1] = "|"
        screen[0, 0] = screen[0, -1] = screen[-1, 0] = screen[-1, -1] = "+"
        return screen

    @staticmethod
    def screen_to_tui(screen):
        """
        Convert a screen to a TUI representation
        :param screen: The screen to convert
        :return: The TUI representation of the screen
        """
        return b"".join(b"".join(chain(row, [b"\r", b"\n"])) for row in screen).decode()
