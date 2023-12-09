import numpy as np
import threading

from itertools import chain
from collections import namedtuple


class Paddle:
    """
    Paddle object for pong
    """

    def __init__(self, row, col, length=1):
        self.row = row
        self.col = col
        self.length = length
        self.direction = 0


class Player:
    """
    Player object for pong
    """

    def __init__(self, paddle):
        self.paddle = paddle
        self.is_ready = False


class Ball:
    SYMBOL = b"*"

    def __init__(self, row, col, row_velocity, col_velocity):
        """
        Initialize the ball with its position and velocity components.
        :param row: The row of the ball.
        :param col: The column of the ball.
        :param row_velocity: The horizontal velocity component of the ball.
        :param col_velocity: The vertical velocity component of the ball.
        """
        self.row = row
        self.col = col
        self.row_velocity = row_velocity
        self.col_velocity = col_velocity

    def update_position(self):
        """
        Update the ball's position based on its velocity.
        """
        self.row += self.row_velocity
        self.col += self.col_velocity

    def invert_row_velocity(self):
        """
        Invert the horizontal velocity to simulate a bounce.
        """
        self.row_velocity *= -1

    def invert_col_velocity(self):
        """
        Invert the vertical velocity to simulate a bounce.
        """
        self.col_velocity *= -1

    def get_col(self):
        return self.col

    def get_row(self):
        return self.row

    def handle_wall_collision(self, rows, cols):
        """
        Check if the ball has collided with a wall.
        :param rows: The number of rows in the game.
        :param cols: The number of columns in the game.
        :return: 1 if the ball has collided with the left (player 1) wall,
                 2 if the ball has collided with the right (player 2) wall,
                 0 otherwise.
        """
        if self.get_col() <= 0:
            return 1
        elif self.get_col() >= cols - 1:
            return 2
        elif self.get_row() <= 0 or self.get_row() >= rows - 1:
            self.invert_row_velocity()
        return 0

    def handle_paddle_collision(self, left_paddle, right_paddle):
        """
        Check if the ball has collided with a paddle.
        :param left/right_paddle: The paddle to check collision with.
        :return: True if the ball has collided with the paddle, False otherwise.
        """
        if (
            left_paddle.col + 1 == self.get_col()
            and left_paddle.row <= self.get_row()
            and self.get_row() <= left_paddle.row + left_paddle.length - 1
        ) or (
            right_paddle.col - 1 == self.get_col()
            and right_paddle.row <= self.get_row()
            and self.get_row() <= right_paddle.row + right_paddle.length - 1
        ):
            self.invert_col_velocity()

    def keep_within_bounds(self, rows, cols):
        self.row = np.clip(self.row, 1, rows - 2)
        self.col = np.clip(self.col, 1, cols - 2)


class Game:
    """
    Game object for pong
    """

    DEFAULT_ROWS = 24
    DEFAULT_COLS = 70

    def __init__(self, rows=DEFAULT_ROWS, cols=DEFAULT_COLS):
        self.nrows = rows
        self.ncols = cols

        self.is_game_started_event = threading.Event()

        self.ball = Ball(
            self.nrows // 2,
            self.ncols // 2,
            1,
            1,
        )

        self.paddle1 = Paddle(self.nrows // 2, 1, 3)
        self.paddle2 = Paddle(self.nrows // 2, self.ncols - 2, 3)

        self.screen = Game.get_blank_screen()
        # Draw the paddles
        self.draw_paddle(self.paddle1)
        self.draw_paddle(self.paddle2)
        # Draw the ball
        self.screen[self.ball.get_row()][self.ball.get_col()] = Ball.SYMBOL

        self.player1 = self.player2 = None
        self.loser = 0

    def draw_paddle(self, paddle):
        self.screen[paddle.row : paddle.row + paddle.length, paddle.col] = b"|"

    def initialize_player(self):
        """Initializes a player. Returns non-zero player id, 0 if game is full."""
        if self.player1 is None:
            self.player1 = Player(self.paddle1)
            return 1
        elif self.player2 is None:
            self.player2 = Player(self.paddle2)
            return 2
        else:
            return 0

    def set_player_ready(self, player_id, is_ready):
        """Sets the player status to either 'ready' or 'not ready'"""
        player = self.player1 if player_id == 1 else self.player2
        print(f"Player {player_id} is : {player}")
        print(f"self.player1: {self.player1}")
        print(f"self.player2: {self.player2}")
        player.is_ready = is_ready
        if self.player1.is_ready and self.player2.is_ready:
            self.is_game_started_event.set()
        # else:
        #     self.is_game_started_event.clear()

    def update_ball(self):
        if self.loser != 0:
            # Game is over, don't update anything
            return
        # Erase the ball from the screen
        self.screen[self.ball.get_row()][self.ball.get_col()] = b" "

        self.ball.update_position()
        self.loser = self.ball.handle_wall_collision(self.nrows, self.ncols)

        self.ball.handle_paddle_collision(self.player1.paddle, self.player2.paddle)

        self.ball.keep_within_bounds(self.nrows, self.ncols)

        # Update the ball position on the screen
        self.screen[self.ball.get_row()][self.ball.get_col()] = Ball.SYMBOL

    def update_paddle(self, player_number: int, key):
        """Updates the paddle positions"""
        if self.loser != 0:
            # Game is over, don't update anything
            return
        player = self.player1 if player_number == 1 else self.player2
        paddle = player.paddle

        # Clear old paddle
        self.screen[paddle.row : paddle.row + paddle.length, paddle.col] = b" "

        # Only update paddle position if the key is valid and the paddle is not at the edge of the screen
        if key == b"w":
            paddle.direction = -1
        elif key == b"s":
            paddle.direction = 1
        elif key == b" ":
            paddle.direction = 0

        if paddle.direction == -1 and paddle.row > 1:
            paddle.row -= 1
        elif paddle.direction == 1 and paddle.row < self.nrows - paddle.length - 1:
            paddle.row += 1

        # Draw new paddle
        self.draw_paddle(paddle)

    def __str__(self):
        return Game.screen_to_tui(self.screen)

    def is_full(self):
        return self.player1 is not None and self.player2 is not None

    @staticmethod
    def get_blank_screen(rows=DEFAULT_ROWS, cols=DEFAULT_COLS):
        """Return a blank screen with no paddles or ball, just the border"""
        screen = np.full((rows, cols), b" ", dtype="S1")
        screen[0, :] = screen[-1, :] = b"-"
        screen[:, 0] = screen[:, -1] = b"+"
        return screen

    @staticmethod
    def screen_to_tui(screen):
        """
        Convert a screen to a TUI representation
        :param screen: The screen to convert
        :return: The TUI representation of the screen
        """
        # Code looks ugly but point is to minimizing use of str "+" operator.
        return b"".join(
            chain.from_iterable(chain(row, [b"\r", b"\n"]) for row in screen)
        ).decode()
