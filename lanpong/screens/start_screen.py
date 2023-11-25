import unicurses


class StartScreen:
    def __init__(self):
        self.stdscreen = None

    def draw(self):
        self.stdscreen = unicurses.initscr()
        unicurses.start_color()

        # Check if the terminal supports colors
        if not unicurses.has_colors():
            unicurses.endwin()
            print("Your terminal does not support color")
            return

        # Define color pair
        unicurses.init_pair(1, unicurses.COLOR_RED, unicurses.COLOR_BLACK)

        # Clear screen
        unicurses.clear()

        # Create a new window
        self.height, self.width = 10, 40  # Define the window size
        start_y, start_x = 4, 4  # Define the position of the window
        self.win = unicurses.newwin(self.height, self.width, start_y, start_x)

        # Box the window and add a title
        unicurses.box(self.win)
        unicurses.mvwaddstr(self.win, 0, 2, " Game Title ")

        # Refresh the screen to show the box
        unicurses.wrefresh(self.win)

    def get_content(self):
        print("getting content...")
        screen_content = ""
        for y in range(self.height):
            for x in range(self.width):
                tmp = unicurses.mvwgetstr(self.win, y, x)
                screen_content += tmp
        print("screen_content: ", screen_content)
