import sublime
import sublime_plugin

class ExpandDeleteWordCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        for sel in self.view.sel():
            self.view.run_command("expand_selection", {"to": "word"})
            self.view.run_command("left_delete")

class ExpandCutWordCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        for sel in self.view.sel():
            self.view.run_command("expand_selection", {"to": "word"})
            self.view.run_command("cut")

class ExpandCutLineCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        for sel in self.view.sel():
            self.view.run_command("expand_selection", {"to": "line"})
            self.view.run_command("cut")
