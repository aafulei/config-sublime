# Move current line to top or center of screen

# modified from https://github.com/mburrows/RecenterTopBottom

import sublime
import sublime_plugin
from itertools import cycle

POSNS = cycle(["top", "middle"])

class CaretWatcher(sublime_plugin.EventListener):
    def on_selection_modified(self, view):
        # caret has moved, reset positions to their default value
        global POSNS
        POSNS = cycle(["top", "middle"])

class ShowAtTopCenterCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        posn = next(POSNS)
        if posn == "top":
            self.show_at_top()
        elif posn == "bottom":
            self.show_at_bottom()
        else:
            self.view.run_command("show_at_center")

    def row(self):
        caret = self.view.sel()[0].begin()
        return self.view.rowcol(caret)[0]

    def show_at_top(self):
        top, _ = self.screen_extents()
        margin = 5
        offset = self.row() - top - margin
        self.view.run_command("scroll_lines", {"amount": -offset})

    def show_at_bottom(self):
        _, bottom = self.screen_extents()
        offset = bottom - self.row() - 1
        self.view.run_command("scroll_lines", {"amount": offset})

    def screen_extents(self):
        screenful = self.view.visible_region()
        top_row, _ = self.view.rowcol(screenful.begin())
        bottom_row, _ = self.view.rowcol(screenful.end())
        return (top_row, bottom_row)
