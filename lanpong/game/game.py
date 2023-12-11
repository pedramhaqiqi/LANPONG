import random
import numpy as np
import threading

from itertools import chain
from collections import namedtuple
import time


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

    def __init__(self, paddle, username):
        self.paddle = paddle
        self.is_ready = False
        self.username = username
        self.id = None


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

        Args:
            left_paddle (Paddle): The left paddle.
            right_paddle (Paddle): The right paddle.

        Returns:
            None. Modifies the ball's velocity if a collision occurs.
        """
        # Check if the ball's column position matches the right edge of the left paddle
        # and if the ball's row position is within the vertical range of the left paddle
        if (
            left_paddle.col + 1 == self.get_col()
            and left_paddle.row <= self.get_row()
            and self.get_row() <= left_paddle.row + left_paddle.length - 1
        ) or (
            # Check if the ball's column position matches the left edge of the right paddle
            # and if the ball's row position is within the vertical range of the right paddle
            right_paddle.col - 1 == self.get_col()
            and right_paddle.row <= self.get_row()
            and self.get_row() <= right_paddle.row + right_paddle.length - 1
        ):
            # If either condition is met, invert the ball's vertical velocity to simulate a bounce
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
    STATS_HEIGHT = 3
    GAME_LENGTH = 3
    SCORE_DISPLAY_TIME = 2

    def __init__(
        self,
        rows=DEFAULT_ROWS,
        cols=DEFAULT_COLS,
        stats_height=STATS_HEIGHT,
        game_length=GAME_LENGTH,
    ):
        self.nrows = rows
        self.ncols = cols
        self.score = [0, 0]
        self.score_timestamp = 0
        self.most_recent_score = -1

        self.is_game_started_event = threading.Event()

        self.ball = Ball(
            self.nrows // 2,
            self.ncols // 2,
            1,
            1,
        )

        self.paddle1 = Paddle(self.nrows // 2, 1, 3)
        self.paddle2 = Paddle(self.nrows // 2, self.ncols - 2, 3)

        self.screen = Game.get_blank_screen(stats_height=stats_height)
        network_header = "Network Statistics:"
        start = (cols - len(network_header)) // 2
        self.screen[-self.STATS_HEIGHT, start : start + len(network_header)] = list(
            network_header
        )
        # Draw the paddles
        self.draw_paddle(self.paddle1)
        self.draw_paddle(self.paddle2)
        # Draw the ball
        self.screen[self.ball.get_row()][self.ball.get_col()] = Ball.SYMBOL

        self.player1 = self.player2 = None

        self.loser = 0

    def _reset_paddles(self):
        """Resets the paddles to their original positions"""
        self.screen[1 : self.nrows - 1, 1] = self.screen[1 : self.nrows - 1, -2] = b" "
        self.paddle1.row = self.nrows // 2
        self.paddle2.row = self.nrows // 2
        self.paddle1.direction = self.paddle2.direction = 0

    def _reset_ball(self):
        """Resets the ball to its original position"""
        self.ball.row = self.nrows // 2
        self.ball.col = self.ncols // 2
        choice = random.choice([-1, 1])
        self.ball.row_velocity *= choice
        self.ball.col_velocity *= choice

    def reset_board(self):
        """Resets the board to its original state"""
        self._reset_paddles()
        self._reset_ball()

    def draw_paddle(self, paddle):
        """Draws a paddle on the screen"""
        self.screen[paddle.row : paddle.row + paddle.length, paddle.col] = b"|"

    def initialize_player(self, username):
        """Initializes a player. Returns non-zero player id, 0 if game is full."""
        if self.player1 is None:
            self.player1 = Player(self.paddle1, username)
            self.player1.id = 1
            return 1
        elif self.player2 is None:
            self.player2 = Player(self.paddle2, username)
            self.player2.id = 2
            return 2
        else:
            return 0

    def set_player_ready(self, player_id, is_ready):
        """Sets the player status to either 'ready' or 'not ready'"""
        player = self.player1 if player_id == 1 else self.player2
        player.is_ready = is_ready
        if self.player1.is_ready and (
            self.player2 is not None and self.player2.is_ready
        ):
            self.is_game_started_event.set()

    def update_score(self, player_id):
        """Updates the score of the player"""
        if player_id != 0:
            self.score[player_id - 1] += 1
            self.check_for_winner()
            self.reset_board()

    def check_for_winner(self):
        """Checks if there is a winner and updates the screen"""
        if self.score[0] >= self.GAME_LENGTH:
            self.loser = 2
        elif self.score[1] >= self.GAME_LENGTH:
            self.loser = 1

    def update_game(self):
        """
        Updates the game state.

        This function handles the main logic for updating the game state, including ball movement,
        collisions, score tracking, and screen updates.

        Returns:
            None. Modifies the internal state of the Game object.
        """
        # Check if the game is in the score display phase after a goal
        if time.time() - self.score_timestamp < self.SCORE_DISPLAY_TIME:
            return

        # Reset the most recent score, indicating no recent score update
        self.most_recent_score = -1

        # Check if the game is over
        if self.loser != 0:
            # Game is over, don't update anything further
            return

        # Erase the ball from its previous position on the screen
        self.screen[self.ball.get_row()][self.ball.get_col()] = b" "

        # Update the ball's position based on its velocity
        self.ball.update_position()

        # Check for collisions with the walls and update the score if a goal is scored
        score = self.ball.handle_wall_collision(self.nrows, self.ncols)
        if score != 0:
            # Record the timestamp of the goal for score display
            self.score_timestamp = time.time()
            # Update the most recent score and overall score
            self.most_recent_score = score
            self.update_score(score)

        # Check for collisions with paddles and adjust ball velocity accordingly
        self.ball.handle_paddle_collision(self.player1.paddle, self.player2.paddle)

        # Ensure the ball stays within the game boundaries
        self.ball.keep_within_bounds(self.nrows, self.ncols)

        # Update the ball position on the screen
        self.screen[self.ball.get_row()][self.ball.get_col()] = Ball.SYMBOL

    def get_message_screen(self, message):
        screen = Game.get_blank_screen(stats_height=0)
        rows, cols = screen.shape
        assert len(message) < cols - 2

        start = (cols - len(message)) // 2
        screen[rows // 2, start : start + len(message)] = list(message)
        return Game.screen_to_tui(screen)

    def update_paddle(self, player_number: int, key):
        """
        Updates the paddle positions based on user input.

        This function handles the paddle movement in response to user input.
        It checks the validity of the input key and ensures that the paddle stays within the game boundaries.

        Args:
            player_number (int): The player number (1 or 2) whose paddle to update.
            key (bytes): The user input key representing the desired paddle movement.

        Returns:
            None. Modifies the internal state of the Game object.
        """
        # Check if the game is in the score display phase after a goal
        if time.time() - self.score_timestamp < self.SCORE_DISPLAY_TIME:
            return

        # Check if the game is over
        if self.loser != 0:
            # Game is over, don't update anything further
            return

        # Select the player and corresponding paddle based on the player number
        player = self.player1 if player_number == 1 else self.player2
        paddle = player.paddle

        # Clear the old paddle position on the screen
        self.screen[paddle.row : paddle.row + paddle.length, paddle.col] = b" "

        # Check if the key is valid and update the paddle direction
        if key == b"w":
            paddle.direction = -1
        elif key == b"s":
            paddle.direction = 1
        elif key == b" ":
            paddle.direction = 0

        # Update the paddle position based on the direction and ensure it stays within bounds
        if paddle.direction == -1 and paddle.row > 1:
            paddle.row -= 1
        elif paddle.direction == 1 and paddle.row < self.nrows - paddle.length - 1:
            paddle.row += 1

        # Draw the new paddle position on the screen
        self.draw_paddle(paddle)

    def update_network_stats(self, stats, offset=1):
        """Updates the network statistics area"""
        # self.screen[-self.STATS_HEIGHT + 1, 1:-2] = b" "
        if offset == 1:
            self.screen[-self.STATS_HEIGHT + 1, 1 : 1 + len(stats)] = list(stats)
        else:
            self.screen[-self.STATS_HEIGHT + 1, -1 - len(stats) : -1] = list(stats)

    def is_full(self):
        """Returns True if the game is full, False otherwise"""
        return self.player1 is not None and self.player2 is not None

    def __str__(self):
        if time.time() - self.score_timestamp < self.SCORE_DISPLAY_TIME:
            return self.get_message_screen(
                f"{self.player1.username if self.most_recent_score == self.player1.id else self.player2.username} scores! Score: {self.score[0]}-{self.score[1]}"
            )

        return Game.screen_to_tui(self.screen)

    @staticmethod
    def get_blank_screen(
        rows=DEFAULT_ROWS, cols=DEFAULT_COLS, stats_height=STATS_HEIGHT
    ):
        """Return a blank screen with no paddles or ball, just the border"""
        rows = rows + stats_height
        screen = np.full((rows, cols), b" ", dtype="S1")
        screen[0, :] = screen[-1, :] = screen[-stats_height - 1, :] = b"-"
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
