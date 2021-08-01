# standard
import datetime
import os
import re
import string
import subprocess
import time
# sublime
import sublime
import sublime_plugin

"""
Change Selection Enpoint
Cycle
Deselect
Expand Cut
Friendly Mark
Git Blame Status Bar
Go to Last Edit
NewFile
Paste From History
Show at Top Center
Subword
"""

# sublime.log_commands(True)

g_debug_on = False
g_trace_on = False
g_debug_log = print if g_debug_on else lambda *args, **kwargs: None
g_trace_log = print if g_trace_on else lambda *args, **kwargs: None

# ===== Global Functions ==============================================================================================

def get_caret_row(view):
    caret = view.sel()[0].begin()
    caret_row = view.rowcol(caret)[0]
    g_trace_log("get_caret_row(): {}".format(caret_row + 1))
    return caret_row

def get_visual_rows(view):
    top_row = view.rowcol(view.visible_region().begin())[0]
    bottom_row = view.rowcol(view.visible_region().end())[0]
    g_trace_log("get_visual_rows(): top {}, bottom {}".format(top_row + 1, bottom_row + 1))
    return top_row, bottom_row

def get_view_file_name(view):
    ret = view.file_name()
    g_trace_log("get_view_file_name(): {}".format(ret))
    return ret

def cycle(sequence):
    while True:
        for elem in sequence:
            yield elem

# ===== Develop =======================================================================================================

class DevelopCommand(sublime_plugin.TextCommand):
    def __init__(self, view):
        super().__init__(view)

    def run(self, edit):
        g_debug_log("develop(): run")

# ===== ToggleLogCommands =======================================================================================================

class ToggleLogCommandsCommand(sublime_plugin.WindowCommand):
    def __init__(self, window):
        super().__init__(window)
        self._toggle = True

    def run(self):
        sublime.log_commands(self._toggle)
        g_debug_log("sublime.log_commands({})".format(self._toggle))
        self._toggle = not self._toggle

# ===== Deselect ======================================================================================================

# # adapted from the deselect plugin by Aristotelis (glutanimate)
# # https://packagecontrol.io/packages/Deselect

# no need to test num_selections when run_command
# class DeselectCommand(sublime_plugin.TextCommand):
#     def run(self, edit):
#         if len(self.view.sel()) == 1:
#             end = self.view.sel()[0].b
#             end_region = sublime.Region(end, end)
#             self.view.sel().clear()
#             self.view.sel().add(end_region)
#         else:
#             self.view.run_command("single_selection")

# ===== Change Selection Enpoint ======================================================================================

# adapted from a forum post by OdatNurd
# https://forum.sublimetext.com/t/move-caret-to-beginning-or-end-of-selection-without-losing-selection/29329

# class ChangeSelectionEndpointCommand(sublime_plugin.TextCommand):
#     def run(self, edit):
#         new_sel = []
#         for region in self.view.sel():
#             new_sel.append(sublime.Region(region.b, region.a))
#         self.view.sel().clear()
#         self.view.sel().add_all(new_sel)

# ===== Cycle =========================================================================================================

# g_last_text_command = ""

# class LastTextCommandUpdater(sublime_plugin.EventListener):
#     def on_post_text_command(self, view, name, args):
#         global g_last_text_command
#         g_last_text_command = name

# class CycleThroughSelectionsCommand(sublime_plugin.TextCommand):
#     def __init__(self, view):
#         super().__init__(view)
#         self.sel = []
#         self.num = 0

#     def run(self, edit, forward=True):
#         if g_last_text_command != self.name():
#             if len(self.view.sel()) == 0:
#                 g_debug_log("no selections. return.")
#                 return
#             else:
#                 self.sel = list(self.view.sel())
#                 self.num = 0 if forward else len(self.sel) - 1
#                 g_debug_log("cycle through {} selection(s)".format(len(self.sel)))
#         self.view.sel().clear()
#         self.view.sel().add(self.sel[self.num])
#         self.view.show(self.sel[self.num])
#         g_debug_log("select {}/{}".format(self.num + 1, len(self.sel)))
#         if forward:
#             self.num = (self.num + 1) % len(self.sel)
#         else:
#             self.num = (self.num - 1) % len(self.sel)

# ===== Show at Top Center ============================================================================================

# adapted from the Recenter​Top​Bottom Sublime Text 2 plugin by Matt Burrows (mburrows)
# https://github.com/mburrows/RecenterTopBottom

g_show_at_positions = ["top", "center"]
g_show_at_generator = cycle(g_show_at_positions)

class CaretWatcher(sublime_plugin.EventListener):
    def on_selection_modified_async(self, view):
        global g_show_at_generator
        g_show_at_generator = cycle(g_show_at_positions)
        g_trace_log("CaretWatcher(): caret has moved, reset g_show_at_generator")

class ShowAtPositionsCommand(sublime_plugin.TextCommand):
    def run(self, edit, margin=5):
        pos = next(g_show_at_generator)
        if pos == "top":
            self.show_at_top(margin)
        elif pos == "bottom":
            self.show_at_bottom(margin)
        else:
            self.view.run_command("show_at_center")
            g_debug_log("show_at_center()")

    def show_at_top(self, margin):
        offset = self.caret_row() - self.top_row() - margin
        self.view.run_command("scroll_lines", {"amount": -offset})
        g_debug_log("show_at_top(margin={}): scroll_lines(amount={})".format(margin, -offset))

    def show_at_bottom(self, margin):
        offset = self.bottom_row() - self.caret_row() - margin
        self.view.run_command("scroll_lines", {"amount": offset})
        g_debug_log("show_at_bottom(margin={}): scroll_lines(amount={})".format(margin, offset))

    def caret_row(self):
        return get_caret_row(self.view)

    def top_row(self):
        return get_visual_rows(self.view)[0]

    def bottom_row(self):
        return get_visual_rows(self.view)[1]

# ===== Git Blame Status Bar ==========================================================================================

# adapted from a gist from Rodrigo Bermúdez Schettino (rodrigobdz)
# https://gist.github.com/rodrigobdz/dbcdcaac6c5af7276c63ec920ba894b0

def get_days_ago(day):
    return (datetime.datetime.now() - day).days

    if ret == 0:
        return "today"
    elif abs(ret) == 1:
        return "{} day ago".format(ret)
    else:
        return "{} days ago".format(ret)

class GitBlameStatusbarCommand(sublime_plugin.EventListener):
    def on_selection_modified_async(self, view):
        caret_row = get_caret_row(view)
        path = get_view_file_name(view)
        if not path:
            return
        blame = self.get_blame(caret_row + 1, path)
        if not blame:
            return
        parsed = self.parse_blame(blame)
        output = ""
        author = parsed.get("author")
        if author:
            output += author
        author_time = parsed.get("author-time")
        if author_time:
            author_datetime = datetime.datetime.fromtimestamp(int(author_time))
            days_ago = get_days_ago(author_datetime)
            if output:
                output += ", "
            if abs(days_ago) <= 1:
                output += "{} day ago".format(days_ago)
            else:
                output += "{} days ago".format(days_ago)
        if output:
            view.set_status("git_blame", "→ " + output)

    def get_blame(self, line, path):
        try:
            # some preparation work for Windows
            startup_info = subprocess.STARTUPINFO()
            startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        except:
            startup_info = None
        working_dir = os.path.dirname(os.path.realpath(path))
        try:
            ret = subprocess.check_output(["git", "blame", "--porcelain", "-L {0},{0}".format(line), path],
                cwd=working_dir,
                startupinfo=startup_info,
                stderr=subprocess.STDOUT)
            return ret.decode()
        except subprocess.CalledProcessError as e:
            error_code = e.returncode
            error_info = e.output.decode()
            g_trace_log("GitBlameStatusbarCommand(): [error code {}] {}".format(error_code, error_info))
        except Exception as e:
            g_trace_log("GitBlameStatusbarCommand(): [unexpected error] {}".format(e))

    def parse_blame(self, blame):
        ret = {}
        for line in blame.splitlines()[1:]:
            # ----------------------------
            # git-blame --porcelain format
            # ----------------------------
            # 1. header line, e.g. commit SHA, original and final line numbers
            # 2. more header info, e.g. author, author-time
            # 3. [TAB] actual content line
            if line.startswith("\t"):
                return ret
            words = line.split()
            if len(words) > 1:
                ret[words[0]] = " ".join(words[1:])
        return ret

# ===== Go to Last Edit ===============================================================================================

# adapted from the GotoLastEditEnhanced plugin by Leonid Shagabutdinov (shagabutdinov)
# see https://github.com/shagabutdinov/sublime-goto-last-edit-enhanced

MAX_HIST_SIZE = 5000

class ViewHistory():
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
        self.views = {}
        self.index = 0

    def get(self, view):
        vid = view.id()
        if vid not in self.views:
            self.views[vid] = ViewHistory()
        return self.views[vid]


collection = Collection()

class GotoLastEditCommand(sublime_plugin.TextCommand):
    def run(self, edit, backward=False):
        history = collection.get(self.view)
        g_debug_log("goto_last_edit(): run on view {}".format(self.view.id()))
        g_debug_log("history.start={}".format(history.start))
        g_debug_log("history.index={}".format(history.index))
        g_debug_log("history.max={}".format(history.max))
        history_range = reversed(range(history.start, history.index + 1))
        if backward:
            history_range = range(history.index, history.max + 1)
        for index in history_range:
            regions = self.view.get_regions("goto_last_edit_" + str(index))
            if self.are_regions_equal(regions, self.view.sel()):
                continue
            if len(regions) > 0:
                self.view.sel().clear()
                self.view.sel().add_all(regions)
                self.view.show(regions[0])
                history.index = index
                break

    def are_regions_equal(self, regions_1, regions_2):
        endpoints_1 = [(r.a, r.b) for r in regions_1]
        endpoints_2 = [(r.a, r.b) for r in regions_2]
        return endpoints_1 == endpoints_2

class ViewWatcher(sublime_plugin.EventListener):
    def on_modified(self, view):
        history = collection.get(view)
        if history.size() >= MAX_HIST_SIZE:
            oldest = history.remove_oldest()
            view.erase_regions("goto_last_edit_" + str(oldest))
        history.increment()
        new_regions_index = "goto_last_edit_{}".format(history.index)
        view.add_regions(new_regions_index, view.sel())
        g_debug_log("add_regions {}".format(new_regions_index))

# ===== Expand Cut ====================================================================================================

class ExpandCutWordCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command("expand_selection", {"to": "word"})
        self.view.run_command("cut")

# class ExpandCopyWordCommand(sublime_plugin.TextCommand):
#     def run(self, edit):
#         old_sel = list(self.view.sel())
#         self.view.run_command("expand_selection", {"to": "word"})
#         self.view.run_command("copy")
#         self.view.sel().clear()
#         self.view.sel().add_all(old_sel)

# class ExpandPasteWordCommand(sublime_plugin.TextCommand):
#     def run(self, edit):
#         self.view.run_command("expand_selection", {"to": "word"})
#         self.view.run_command("paste")

# ===== Simple Mark ===================================================================================================

# class SelectWithMarkCommand(sublime_plugin.TextCommand):
#     def run(self, edit):
#         self.view.run_command("select_to_mark")
#         self.view.run_command("change_selection_endpoint")
#         self.view.run_command("clear_bookmarks", {"name": "mark"})

# class CutToMarkCommand(sublime_plugin.TextCommand):
#     def run(self, edit):
#         self.view.run_command("select_with_mark")
#         self.view.run_command("cut")

# class CopyToMarkCommand(sublime_plugin.TextCommand):
#     def run(self, edit):
#         old_sel = list(self.view.sel())
#         self.view.run_command("select_with_mark")
#         self.view.run_command("copy")
#         self.view.sel().clear()
#         self.view.sel().add_all(old_sel)

# class PasteToMarkCommand(sublime_plugin.TextCommand):
#     def run(self, edit):
#         self.view.run_command("select_with_mark")
#         self.view.run_command("paste")

# class GoToMarkCommand(sublime_plugin.TextCommand):
#     def run(self, edit):
#         self.view.run_command("next_bookmark", {"name": "mark"})
#         self.view.run_command("clear_bookmarks", {"name": "mark"})

# ===== Paste From History ============================================================================================

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

# ===== Subword =======================================================================================================

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

# ===== NewFile =======================================================================================================

# Save a new file to the current folder by default

# bugs:
# typeof= <class 'NoneType'>
# Traceback (most recent call last):
#   File "/Applications/Sublime Text.app/Contents/MacOS/sublime_plugin.py", line 428, in on_new_async
#     callback.on_new_async(v)
#   File "/Users/aa/Library/Application Support/Sublime Text 3/Packages/My New File/new_file.py", line 17, in on_new_async
#     view.settings().set("default_dir", view.window().folders()[0])
# AttributeError: 'NoneType' object has no attribute 'folders'

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


g_find_whole_word = True
g_find_case_sensitive = True

class FindStatusbarCommand(sublime_plugin.EventListener):
    def on_post_text_command(self, view, name, args):
        if g_find_case_sensitive:
            find_case_sensitive_s = "C"
        else:
            find_case_sensitive_s = "~c"
        if g_find_whole_word:
            find_whole_word_s = "W"
        else:
            find_whole_word_s = "~w"
        find_status = "[" + find_case_sensitive_s + "] [" + find_whole_word_s + "]"
        view.set_status("find_status", find_status)

class ToggleFindWholeWordCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global g_find_whole_word
        g_find_whole_word = not g_find_whole_word

class ToggleFindCaseSensitiveCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global g_find_case_sensitive
        g_find_case_sensitive = not g_find_case_sensitive



import sublime
import sublime_plugin

class ExpandSelectionToLineUpwardsCommand(sublime_plugin.TextCommand):
    def run(self, edit, reverse=False):
        # enable soft-undo line by line
        sublime.set_timeout(lambda:
            self.view.run_command("expand_selection_to_line_upwards_atomic",
                                 {"reverse": reverse}),
            0)

class ExpandSelectionToLineUpwardsAtomicCommand(sublime_plugin.TextCommand):
    def run(self, edit, reverse):
        for region in self.view.sel():
            region_begin = region.begin()
            region_end = region.end()
            line_begin = self.view.line(region_begin).begin()
            line_end = self.view.line(region_end).end()
            # expand to one line below / above if this line has been covered
            covered = line_begin == region_begin and line_end == region_end
            if reverse:
                line_end = self.view.line(region_end + covered).end()
                new_region = sublime.Region(line_begin, line_end)
            else:
                line_begin = self.view.line(region_begin - covered).begin()
                new_region = sublime.Region(line_end, line_begin)
            self.view.sel().add(new_region)
