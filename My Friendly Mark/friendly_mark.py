import sublime
import sublime_plugin

class SelectWithMarkCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        origPoint = self.view.sel()[-1].begin()
        self.view.run_command("next_bookmark", {"name": "mark"})
        markPoint = self.view.sel()[0].begin()
        self.view.sel().clear()
        self.view.sel().add_all([sublime.Region(markPoint, origPoint)])

class CopyToMarkCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        origPoint = self.view.sel()[-1].begin()
        self.view.run_command("next_bookmark", {"name": "mark"})
        markPoint = self.view.sel()[0].begin()
        self.view.sel().clear()
        self.view.sel().add_all([sublime.Region(markPoint, origPoint)])
        self.view.run_command("copy")

class CutToMarkCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        origPoint = self.view.sel()[-1].begin()
        self.view.run_command("next_bookmark", {"name": "mark"})
        markPoint = self.view.sel()[0].begin()
        self.view.sel().clear()
        self.view.sel().add_all([sublime.Region(markPoint, origPoint)])
        self.view.run_command("cut")

class GoToMarkCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command("next_bookmark", {"name": "mark"})

