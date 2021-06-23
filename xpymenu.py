#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# A versatile Dmenu clone written in Python3
# It grabs user input until any non-acceped key has been pressed
#
# Author: Irreq

from Xlib import X, XK

from Xlib.display import Display

# START CONFIG

COLORMAP = {"red": "#ff0000",
            "green": "#00ff00",
            "blue": "#0000ff",
            "white": "#ffffff",
            "black_old": "#000000",
            "black": "#cad624",
            }

FONT_NAME = '-PxPlus-HP-100LX-10x11'
FONT_WIDTH = 6 # Working on my computer
FONT_HEIGHT = 16

# Note that space is the first character
ACCEPTED_KEYS = " abcdefghijklmnopqrstuvwxyz"

# END CONFIG

running = True


def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i+lv//3], 16) for i in range(0, lv, lv//3))


def stop():
    global running
    running = False


class Window():
    """Front-end handling the visual side. Can be used to display anything"""
    gcs = {}
    monitor = None

    def __init__(self):
        self.disp = Display()
        self.screen = self.disp.screen()
        self.width, self.height = self.screen.width_in_pixels, FONT_HEIGHT

        self.x = 0
        self.y = 0

        self.window = self.create_window(self.disp)
        self.load_colormap()

    def clear(self, window):
        """Erase the window WINDOW."""
        geom = window.get_geometry()
        window.clear_area(0, 0, geom.width, geom.height)

    def screen_flush(self, screen):
        screen.default_colormap.alloc_named_color('white')

    def create_window(self, override=1, mask=X.ExposureMask):
        """Create a new window on screen SCREEN in display DISP with given
        WIDTH and HEIGHT, which is placed at the geometry of (X, Y) using
        Xlib's XCreateWindow. override_redirect and event_mask can specified
        by OVERRIDE and MASK, respectively."""
        window = self.screen.root.create_window(
            self.x,
            self.y,
            self.width,
            self.height,
            0,
            self.screen.root_depth,
            X.InputOutput,
            X.CopyFromParent,
            background_pixel=self.screen.black_pixel,
            override_redirect=override,
            event_mask=mask,
            colormap=X.CopyFromParent,
        )
        window.change_attributes(backing_store=X.Always)
        window.map()
        return window

    def load_colormap(self):
        """Create GCs (Graphics Content) on screen SCREEN in display DISP for
        window WINDOW with font FONT.  GCs are returned as a dictionary, whose
        key is the color name (e.g., 'black') and the value is a dictionary,
        whose items are (LEVEL, GC), where LEVEL is a brightness between 0 and
        100 and GC is the GC for that brightness."""

        for color in COLORMAP:
            (red, green, blue) = hex_to_rgb(COLORMAP[color])
            self.gcs[color] = {}
            for level in range(100 + 1):
                r = int(red * level / 100)
                g = int(green * level / 100)
                b = int(blue * level / 100)
                pixel = (r << 16) | (g << 8) | b
                # self.gcs[color][level] = self.window.create_gc(font=self.font,
                #                                                foreground=pixel)
                self.gcs[color][level] = self.window.create_gc(foreground=pixel)

    def draw_str(self, astr, col=0, row=0, color='white', level=100,
                 reverse=False):
        """Render a string ASTR on window WINDOW on screen SCREEN in display
        DISP using graphics contents GC.  Text color and brightness can be
        specified by COLOR and LEVEL, respectively. Reverse video is enabled
        if REVERSE is True."""
        fgcolor, bgcolor = color, 'black'
        if reverse:
            fgcolor, bgcolor = bgcolor, fgcolor
        x = col * FONT_WIDTH
        y = row * FONT_HEIGHT
        w = FONT_WIDTH * len(astr)
        h = FONT_HEIGHT
        self.window.fill_rectangle(self.gcs[bgcolor][level], x, y, w, h)
        # convert string to list of single bytes
        chars = [c.encode() for c in list(astr)]
        self.window.poly_text(self.gcs[fgcolor][level],
                              x,
                              y + FONT_HEIGHT - 1,
                              chars)

    def draw(self, text):
        self.width = int(FONT_WIDTH*len(text))
        self.window.configure(width=self.width)

        self.clear(self.window)

        self.draw_str(self.text, 0, 0, color="white", reverse=False)

        self.screen_flush(self.screen)
        self.window.configure(stack_mode=X.Above)


class Menu(Window):
    """Backend menu handling the logic and grabbing of keyboard"""
    available = []
    chosen = ""
    root = None
    root_display = None
    user_input = ""
    cursor_position = 0

    def __init__(self, options: list(), separator=" ", max_suggestions=10,
                 keys=ACCEPTED_KEYS):
        super().__init__()
        self.options = options
        self.separator = separator
        self.max_suggestions = max_suggestions
        self.keys = keys
        self.flush()
        self._update()

    def flush(self):
        if self.chosen != "":
            self.user_input = self.chosen

        self.chosen = ""
        self.current_query = self.options.copy()

    def _update(self):

        # self.text = self.archived_input or self.user_input
        self.text = self.user_input

        self.available = [k for k in self.current_query if self.text in k]
        self.available.sort()

        if self.cursor_position < len(self.text):
            self.chosen = ""

            txt1 = self.text[:self.cursor_position]
            txt2 = self.text[self.cursor_position]
            txt3 = self.text[self.cursor_position + 1:]

            self.text = "{0}'{1}{2}".format(txt1, txt2, txt3)

        # Will display the alternatives as suggestions
        elif len(self.text) + 1 <= self.cursor_position <= len(self.text) + len(self.available):
            self.chosen = self.available[int(self.cursor_position-len(self.text)-1)]

        if self.chosen != "":
            self.text = self.chosen

        if self.available:
            self.text += " | " + f"{self.separator}".join(self.available[:self.max_suggestions]) + " | "

        super().draw(self.text)

    def _cursor_to_left(self):
        # Move cursor to left, if possible
        if self.cursor_position:
            self.cursor_position -= 1

    def _cursor_to_right(self):
        # move cursor to right, if possible
        # command = self.archived_input or self.user_input
        command = self.user_input

        if self.cursor_position < len(command) + len(self.available):
            self.cursor_position += 1

    def _insert_key_pos(self, key, pos=0):
        if 0 <= self.cursor_position <= len(self.user_input):
            self.user_input = self.user_input[:self.cursor_position + pos] + key + self.user_input[self.cursor_position + pos:]
            self._cursor_to_right()

    def _delete_key_pos(self, pos=0):
        if 0 <= self.cursor_position <= len(self.user_input):
            self.user_input = self.user_input[:self.cursor_position + pos] + self.user_input[self.cursor_position + pos + 1:]
            if pos == -1:
                self._cursor_to_left()

    def _handle_event(self, event):
        """Handles when key has been released"""
        if (event.type == X.KeyRelease):
            code = self.root_display.keycode_to_keysym(event.detail, 0)
            key = str(XK.keysym_to_string(code))

            if key in self.keys:
                self._insert_key_pos(key, pos=0)
            elif code == 65535:  # Delete
                self._delete_key_pos(pos=0)
            elif code == 65288:  # Backslash
                self._delete_key_pos(pos=-1)
            elif code == 65363:  # Right
                self._cursor_to_right()
            elif code == 65361:  # Left
                self._cursor_to_left()
            elif code == 65293:  # Return
                stop()
            else:
                self.user_input = ""
                stop()

            return

    def _grab_root_events(self):
        self.root_display = Display()
        self.root = self.root_display.screen().root

        # we tell the X server we want to catch keyPress event
        self.root.change_attributes(event_mask=X.KeyPressMask | X.KeyReleaseMask)

        for key in self.keys.split():
            self.root.grab_key(self.root_display.keysym_to_keycode(XK.string_to_keysym(key)), 0, True, X.GrabModeSync, X.GrabModeSync)

        while running:
            event = self.root_display.next_event()
            self._handle_event(event)
            self.root_display.allow_events(X.AsyncKeyboard, X.CurrentTime)
            self._update()

    def start(self):
        self._grab_root_events()
        return self.chosen or self.user_input


if __name__ == "__main__":

    # If you want to run it from the terminal
    # Usage: python3 pmenu.py foo bar lol
    # Then you will get the arguments as options, and
    # The returned string is the choosen argument.

    import sys

    menu = Menu(options=sys.argv[1:])

    result = menu.start()

    print(result)
