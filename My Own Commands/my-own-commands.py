import re
import string

import sublime
import sublime_plugin


# ===== Expand Cut ====================================================================================================

class ExpandCutWordCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command("expand_selection", {"to": "word"})
        self.view.run_command("cut")

class ExpandCopyWordCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        old_sel = list(self.view.sel())
        self.view.run_command("expand_selection", {"to": "word"})
        self.view.run_command("copy")
        self.view.sel().clear()
        self.view.sel().add_all(old_sel)

class ExpandPasteWordCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command("expand_selection", {"to": "word"})
        self.view.run_command("paste")

# ===== Friendly Mark =================================================================================================

class SelectWithMarkCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command("select_to_mark")
        self.view.run_command("change_selection_endpoint")
        self.view.run_command("clear_bookmarks", {"name": "mark"})

class CutToMarkCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command("select_with_mark")
        self.view.run_command("cut")

class CopyToMarkCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        old_sel = list(self.view.sel())
        self.view.run_command("select_with_mark")
        self.view.run_command("copy")
        self.view.sel().clear()
        self.view.sel().add_all(old_sel)

class PasteToMarkCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command("select_with_mark")
        self.view.run_command("paste")

class GoToMarkCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command("next_bookmark", {"name": "mark"})
        self.view.run_command("clear_bookmarks", {"name": "mark"})

# =====================================================================================================================

class ClipboardHistory2():
    """
    Stores the current paste history
    """

    LIST_LIMIT = 15

    def __init__(self):
        self.storage = []

    def push_text(self, text):
        # print("pushed text: ", text)
        if not text:
            return

        DISPLAY_LEN = 45

        # create a display text out of the text
        display_text = re.sub(r'[\n]', '', text)
        # trim all starting space/tabs
        display_text = re.sub(r'^[\t\s]+', '', display_text)
        display_text = (display_text[:DISPLAY_LEN] + '...') if len(display_text) > DISPLAY_LEN else display_text

        self.del_duplicate(text)
        self.storage.insert(0, (display_text, text))

        if len(self.storage) > self.LIST_LIMIT:
            del self.storage[self.LIST_LIMIT:]

    def get(self):
        return self.storage

    def del_duplicate(self, text):
        # remove all dups
        self.storage = [s for s in self.storage if s[1] != text]

    def empty(self):
        return len(self.storage) == 0


g_clipboard_history = ClipboardHistory2()


class ClipboardHistoryUpdater(sublime_plugin.EventListener):
    """
    Listens on the sublime text events and push the clipboard content into the
    ClipboardHistory object
    """

    def on_post_text_command(self, view, name, args):
        if view.settings().get('is_widget'):
            return

        # if name == 'copy' or name == 'cut' or name == "expand_cut_word":
        if name in ["copy", "cut", "expand_cut_word", "expand_copy_word", "expand_cut_subword", "expand_copy_subword", "cut_to_mark", "copy_to_mark", "cut_to_bol", "cut_to_eol"]:
            # print("listened")
            # print("clipboard:", sublime.get_clipboard())
            g_clipboard_history.push_text(sublime.get_clipboard())


class PasteFromHistoryCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # print("Calling PasteFromHistoryCommand from My Expand Cut")
        if self.view.settings().get('is_widget'):
            return

        # provide paste choices
        paste_list = g_clipboard_history.get()
        keys = [x[0] for x in paste_list]
        self.view.show_popup_menu(keys, lambda choice_index: self.paste_choice(choice_index))

    def is_enabled(self):
        return not g_clipboard_history.empty()

    def paste_choice(self, choice_index):
        if choice_index == -1:
            return
        # use normal paste command
        text = g_clipboard_history.get()[choice_index][1]

        # rotate to top
        g_clipboard_history.push_text(text)

        sublime.set_clipboard(text)
        self.view.run_command("paste")



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



class ExpandCopySubwordCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        oldsel = list(self.view.sel())
        self.view.run_command("expand_selection_to_subword")
        self.view.run_command("copy")
        self.view.sel().clear()
        self.view.sel().add_all(oldsel)

class ExpandCutSubwordCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command("expand_selection_to_subword")
        self.view.run_command("cut")


class ExpandPasteSubwordCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command("expand_selection_to_subword")
        self.view.run_command("paste")

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
            # print("no need to cycle")
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
        # print("on_post_text_command:", name)
        if name != "cycle":
            # print("last command is not cycle. clear cache.")
            gcs.init = False
            gcs.sel = []
        else:
            # print("last command is cycle. continue to cycle.")
            pass

# modified from https://github.com/mburrows/RecenterTopBottom
# Move current line to top or center of screen

# import sublime
# import sublime_plugin

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




# Go to last edit position

# modified from https://github.com/shagabutdinov/sublime-goto-last-edit-enhanced

import sublime
import sublime_plugin

MAX_HIST_SIZE = 5000

class History():
    def __init__(self):
        self.index = 0
        self.start = 0
        self.max = 0

    def remove_oldest(self):
        self.start = self.start + 1
        return (self.start - 1)

    def increment(self):
        self.max += 1
        self.index = self.max

    def size(self):
        return self.max - self.start


class Collection():
    def __init__(self):
        self.list = {}
        self.index = 0

    def get(self, view):
        id = view.id()
        if id not in self.list:
            self.list[id] = History()

        return self.list[id]

collection = Collection()

class GotoLastEdit(sublime_plugin.TextCommand):
    def run(self, edit, backward = False):
        history = collection.get(self.view)
        history_range = reversed(range(history.start, history.index + 1))
        if backward:
            history_range = range(history.index, history.max + 1)

        for index in history_range:
            regions = self.view.get_regions('goto_last_edit_' + str(index))
            if self.is_regions_equal(regions, self.view.sel()):
                continue

            if len(regions) > 0:
                self.view.sel().clear()
                self.view.sel().add_all(regions)
                self.view.show(regions[0])
                history.index = index
                break

    def is_regions_equal(self, regions_1, regions_2):
        if len(regions_1) != len(regions_2):
            return False

        for index, region_1 in enumerate(regions_1):
            region_2 = regions_2[index]
            if region_2.a != region_1.a or region_2.b != region_1.b:
                return False

        return True

class Listener(sublime_plugin.EventListener):
    def on_modified(self, view):
        history = collection.get(view)
        if history.size() >= MAX_HIST_SIZE:
            oldest = history.remove_oldest()
            view.erase_regions('goto_last_edit_' + str(oldest))

        history.increment()
        view.add_regions('goto_last_edit_' + str(history.index), view.sel())











# https://gist.github.com/rodrigobdz/dbcdcaac6c5af7276c63ec920ba894b0

import sublime
import sublime_plugin
import os
import subprocess
from subprocess import check_output as shell
from datetime import datetime

try:
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
except:
    si = None

class GitBlameStatusbarCommand(sublime_plugin.EventListener):
  def parse_blame(self, blame):
    sha, file_path, user, date, time, tz_offset, *_ = blame.decode('utf-8').split()

    # Was part of the inital commit so no updates
    if file_path[0] == '(':
        user, date, time, tz_offset = file_path, user, date, time
        file_path = None

    # Fix an issue where the username has a space
    # Im going to need to do something better though if people
    # start to have multiple spaces in their names.
    if not date[0].isdigit():
        user = "{0} {1}".format(user, date)
        date, time = time, tz_offset

    return(sha, user[1:], date, time)

  def get_blame(self, line, path):
    try:
        return shell(["git", "blame", "--minimal", "-w",
            "-L {0},{0}".format(line), path],
            cwd=os.path.dirname(os.path.realpath(path)),
            startupinfo=si,
            stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        pass
        # print("Git blame: git error {}:\n{}".format(e.returncode, e.output.decode("UTF-8")))
    except Exception as e:
        pass
        # print("Git blame: Unexpected error:", e)

  def days_between(self, d):
    # now = datetime.strptime(datetime.now(), "%Y-%m-%d")
    now = datetime.now()
    d = datetime.strptime(d, "%Y-%m-%d")
    return abs((now - d).days)

  def on_selection_modified_async(self, view):
    current_line = view.substr(view.line(view.sel()[0]))
    (row,col) = view.rowcol(view.sel()[0].begin())
    path = view.file_name()
    blame = self.get_blame(int(row) + 1, path)
    output = ''
    if blame:
        sha, user, date, time = self.parse_blame(blame)
        # try:
        #     time = '( ' + str(self.days_between(time)) + ' days ago )'
        # except Exception as e:
        #     time = ''
        #     print("Git blame: days_between ", e)
        time = ''
        output = '→ ' + user + ' ' + time

    view.set_status('git_blame', output)









# Save a new file to the current folder by default

# bugs:
# typeof= <class 'NoneType'>
# Traceback (most recent call last):
#   File "/Applications/Sublime Text.app/Contents/MacOS/sublime_plugin.py", line 428, in on_new_async
#     callback.on_new_async(v)
#   File "/Users/aa/Library/Application Support/Sublime Text 3/Packages/My New File/new_file.py", line 17, in on_new_async
#     view.settings().set("default_dir", view.window().folders()[0])
# AttributeError: 'NoneType' object has no attribute 'folders'

import sublime_plugin

class NewFileListener(sublime_plugin.EventListener):
    def on_new_async(self, view):
        if not view.window():
            return
        if view.window() is None:
            print("note - view.window() is None here")
            return
        try:
            if not view.window().folders():
                return
        except AttributeError:
            print("typeof=", type(view.window()))
        view.settings().set("default_dir", view.window().folders()[0])



# Sublime Deselect plugin
#
# based on a forum post by C0D312:
# https://www.sublimetext.com/forum/viewtopic.php?f=2&t=4716#p21219

import sublime, sublime_plugin

class DeselectCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        end = self.view.sel()[0].b
        pt = sublime.Region(end, end)
        self.view.sel().clear()
        self.view.sel().add(pt)
