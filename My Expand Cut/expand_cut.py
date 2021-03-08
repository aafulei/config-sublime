import sublime
import sublime_plugin

import re
import string

def classify(c):
    if c in "_\n":
        return c
    if c in string.ascii_lowercase:
        return "a"
    if c in string.ascii_uppercase:
        return "A"
    if c in string.digits:
        return "1"
    if c in string.punctuation:
        return "."
    if c in string.whitespace:
        return " "
    return "?"

def is_subword_end(pos, view):
    substr = view.substr(sublime.Region(pos - 1, pos + 1))
    if len(substr) < 2:
        print("For subword end, substr='{}'".format(substr))
        return True

    kind = classify(substr[0]) + classify(substr[1])
    if kind[1] == "\n":
        return True
    if kind[1] == " " and kind[0] != " ":
        return True
    if kind [1] == "_" and kind[0] in "aA1.":
        return True
    if kind in ["aA", "a ", "a.", "a ", "1A", "1.", "1 ", ".?", ".a", ".A", ".1", ". "]:
        return True
    if kind == "AA":
        extra = view.substr(sublime.Region(pos + 1, pos + 2))
        if classify(extra) == "a":
            return True
    if kind in ["A1", "A?"]:
        extra = view.substr(sublime.Region(pos - 2, pos - 1))
        if classify(extra) == "A":
            return True
    return False

def is_subword_begin(pos, view):
    substr = view.substr(sublime.Region(pos - 1, pos + 1))
    if len(substr) < 2:
        print("For subword begin, substr='{}'".format(substr))
        return True

    kind = classify(substr[0]) + classify(substr[1])
    if kind[0] == "\n":
        return True
    if kind[0] == " " and kind[1] != " ":
        return True
    if kind [0] == "_" and kind[1] in "aA1.":
        return True
    if kind in ["aA", "a.", "A.", "1A", "1.", ".?", ".a", ".A", ".1", " a", " A", " 1", " ."]:
        return True
    if kind == "AA":
        extra = view.substr(sublime.Region(pos + 1, pos + 2))
        if classify(extra) == "a":
            return True
    if kind in ["A1", "A?"]:
        extra = view.substr(sublime.Region(pos - 2, pos - 1))
        if classify(extra) == "A":
            return True
    return False

class ExpandSelectionToSubwordCommand(sublime_plugin.TextCommand):
    def run(self, edit, prefer_forwards=True):
        oldsel = list(self.view.sel())
        newsel = []
        for region in oldsel:
            self.view.sel().clear()
            self.view.sel().add(region)
            region = self.view.sel()[0]
            beg = region.begin()
            end = region.end()
            single = beg == end
            pos = beg
            sb = is_subword_begin(pos, self.view)
            print("is_subword_begin:", sb)
            if not sb:
                if region.a < region.b:
                    region.a, region.b = region.b, region.a
                self.view.sel().add(region)
                self.view.run_command("move", { "by": "subwords", "forward": False, "extend": True })

            if region.a > region.b:
                region.a, region.b = region.b, region.a
            self.view.sel().add(region)
            pos = end
            se = is_subword_end(pos, self.view)
            print("is_subword_end:", se)
            if not se:
                self.view.run_command("move", { "by": "subword_ends", "forward": True, "extend": True })
            if single and sb and se:
                substr = self.view.substr(sublime.Region(pos - 1, pos + 1))
                if len(substr) < 2:
                    print("Warning: Touching BOF or EOF.")
                    newsel.append(self.view.sel()[0])
                    continue
                kind = classify(substr[0]) + classify(substr[1])
                extend_forwards = True
                if kind in ["aA", "1A"]:
                    extend_forwards = prefer_forwards
                if kind[1] == ".":
                    extend_forwards = False
                if extend_forwards:
                    self.view.run_command("move", { "by": "subword_ends", "forward": True, "extend": True })
                else:
                    self.view.run_command("move", { "by": "subwords", "forward": False, "extend": True })
                if region.a > region.b:
                    region.a, region.b = region.b, region.a
                self.view.sel().add(region)
            newsel.append(self.view.sel()[0])
        self.view.sel().clear()
        self.view.sel().add_all(newsel)

class CutToEolCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command("move_to", { "to": "hardeol", "extend": True })
        self.view.run_command("cut")

# class ExpandIncrementalFindWordCommand(sublime_plugin.TextCommand):
#     def run(self, edit):
#         self.view.run_command("expand_selection", {"to": "word"})
#         self.view.run_command("copy")
#         self.view.run_command("change_selection_endpoint")
#         self.view.run_command("show_panel", { "panel": "find_in_files", "reverse": False, "toggle": True })
        # self.view.run_command("paste")

class ExpandCopyWordCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        oldsel = list(self.view.sel())
        self.view.run_command("expand_selection", {"to": "word"})
        self.view.run_command("copy")
        self.view.sel().clear()
        self.view.sel().add_all(oldsel)

class ExpandCopySubwordCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        oldsel = list(self.view.sel())
        self.view.run_command("expand_selection_to_subword")
        self.view.run_command("copy")
        self.view.sel().clear()
        self.view.sel().add_all(oldsel)

class ExpandCutWordCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command("expand_selection", {"to": "word"})
        self.view.run_command("cut")

class ExpandCutSubwordCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command("expand_selection_to_subword")
        self.view.run_command("cut")

class ExpandPasteWordCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command("expand_selection", {"to": "word"})
        self.view.run_command("paste")

class ExpandPasteSubwordCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command("expand_selection_to_subword")
        self.view.run_command("paste")

class ExpandDeleteWordCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command("expand_selection", {"to": "word"})
        self.view.run_command("left_delete")


class SelectWithMarkCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        origPoint = self.view.sel()[-1].begin()
        self.view.run_command("next_bookmark", {"name": "mark"})
        markPoint = self.view.sel()[0].begin()
        self.view.sel().clear()
        self.view.sel().add_all([sublime.Region(markPoint, origPoint)])
        self.view.run_command("clear_bookmarks", {"name": "mark"})

class CopyToMarkCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # origPoint = self.view.sel()[-1].begin()
        # self.view.run_command("next_bookmark", {"name": "mark"})
        # markPoint = self.view.sel()[0].begin()
        # self.view.sel().clear()
        # self.view.sel().add_all([sublime.Region(markPoint, origPoint)])
        # self.view.run_command("copy")
        # # g_clipboard_history.push_text(sublime.get_clipboard())
        # self.view.run_command("clear_bookmarks", {"name": "mark"})
        oldsel = list(self.view.sel())
        self.view.run_command("select_with_mark")
        self.view.run_command("copy")
        self.view.sel().clear()
        self.view.sel().add_all(oldsel)

class PasteToCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command("select_with_mark")
        self.view.run_command("paste")


class CutToMarkCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        origPoint = self.view.sel()[-1].begin()
        self.view.run_command("next_bookmark", {"name": "mark"})
        markPoint = self.view.sel()[0].begin()
        self.view.sel().clear()
        self.view.sel().add_all([sublime.Region(markPoint, origPoint)])
        # there is no need to use yank, just ctrl+v to paste
        self.view.run_command("cut")
        # g_clipboard_history.push_text(sublime.get_clipboard())
        self.view.run_command("clear_bookmarks", {"name": "mark"})

class GoToMarkCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command("next_bookmark", {"name": "mark"})
        self.view.run_command("clear_bookmarks", {"name": "mark"})


# https://forum.sublimetext.com/t/move-caret-to-beginning-or-end-of-selection-without-losing-selection/29329/2

# OdatNurd




class ChangeSelectionEndpointCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        new_sel = []
        for sel in self.view.sel():
            # reverse = (sel.a < sel.b) if begin else (sel.b < sel.a)
            reverse = True
            new_sel.append(sublime.Region(sel.b, sel.a) if reverse else sel)
        self.view.sel().clear()
        self.view.sel().add_all(new_sel)


class GlobalCycleState:
    def __init__(self):
        self.init = False
        self.sel = []
        self.num = 0

gcs = GlobalCycleState()

class CycleCommand(sublime_plugin.TextCommand):
    def run(self, edit, forward=True):
        global gcs
        if not gcs.init and len(self.view.sel()) <= 1:
            print("no need to cycle")
            return
        if not gcs.init:
            gcs.sel = list(self.view.sel())
            gcs.init = True
            gcs.num = 0 if forward else len(gcs.sel) - 1
            print("{} selections".format(len(gcs.sel)))
        caret = gcs.sel[gcs.num].begin()
        row = self.view.rowcol(caret)[0]
        print("row at {}".format(row))
        upper, _ = self.view.rowcol(self.view.visible_region().begin())
        bottom,  _ = self.view.rowcol(self.view.visible_region().end())
        print("upper at {}, bottom at {}".format(upper, bottom))
        if row < upper + 5:
            print("row < upper")
            self.view.run_command("scroll_lines", {"amount": upper - row + 5})
        if row > bottom - 5:
            print("row > bottom")
            self.view.run_command("scroll_lines", {"amount": upper - row + 5})
        self.view.sel().clear()
        self.view.sel().add(gcs.sel[gcs.num])
        if forward:
            gcs.num += 1
            if gcs.num == len(gcs.sel):
                gcs.num = 0
        else:
            gcs.num -= 1
            if gcs.num == -1:
                gcs.num = len(gcs.sel) - 1

class LastCommandUpdater(sublime_plugin.EventListener):
    def on_post_text_command(self, view, name, args):
        global gcs
        print("on_post_text_command:", name)
        if name != "cycle":
            print("last command is not cycle. clear cache.")
            gcs.init = False
            gcs.sel = []
        else:
            print("last command is cycle. continue to cycle.")
