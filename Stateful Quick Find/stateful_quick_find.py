import sublime
import sublime_plugin

# g_find_status_set = False
g_find_whole_word = False
g_find_case_sensitive = False


def get_caret_row(view, index=0):
    try:
        caret = view.sel()[index].begin()
    except IndexError:
        return None
    caret_row = view.rowcol(caret)[0]
    return caret_row


def get_visual_rows(view):
    top_row = view.rowcol(view.visible_region().begin())[0]
    bottom_row = view.rowcol(view.visible_region().end())[0]
    return top_row, bottom_row


class FindStatusbarCommand(sublime_plugin.EventListener):
    def on_post_text_command(self, view, command_name, args):
        # global g_find_status_set
        # commands = ["toggle_find_whole_word", "toggle_find_case_sensitive"]
        # if g_find_status_set and command_name not in commands:
        #     return
        c = w = ""
        if g_find_case_sensitive:
            c = "[C]"
        if g_find_whole_word:
            w = "[W]"
        status = "{}{}".format(c, w)
        view.set_status("find_status", status)
        # g_find_status_set = True


class ToggleFindCaseSensitiveCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global g_find_case_sensitive
        g_find_case_sensitive = not g_find_case_sensitive


class ToggleFindWholeWordCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global g_find_whole_word
        g_find_whole_word = not g_find_whole_word


# class DevelopListener(sublime_plugin.EventListener):
#     def on_post_text_command(self, view, command_name, args):
#         if command_name != "develop":
#             view.erase_regions("current_region")

class DevelopCommand(sublime_plugin.TextCommand):
    def __init__(self, view):
        super().__init__(view)

    def caret_row(self):
        return get_caret_row(self.view, index=-1)

    def top_row(self):
        return get_visual_rows(self.view)[0]

    def bottom_row(self):
        return get_visual_rows(self.view)[1]

    def run(self, edit):
        if not self.view.sel():
            return
        region = self.view.sel()[-1]
        single = region.a == region.b
        if single:
            self.view.run_command("expand_selection", {"to": "word"})
        text = self.view.substr(region)
        flags = 0
        if not g_find_case_sensitive:
            flags |= sublime.IGNORECASE
        pattern = text
        if g_find_whole_word:
            pattern = "\\b{}\\b".format(text)
        next_region = self.view.sel()[-1]
        # print(f"{region=}, {next_region=}")
        if not single:
            next_region = self.view.find(pattern, region.b, flags)
            if next_region == sublime.Region(-1, -1):
                next_region = self.view.find(pattern, 0, flags)
        if next_region == sublime.Region(-1, -1):
            return
        self.view.sel().subtract(region)
        self.view.sel().add(next_region)
        self.view.add_regions("current_region", [next_region], scope="string", icon="circle")
        caret_row = self.caret_row()
        if caret_row is None:
            return
        top_row = self.top_row()
        bottom_row = self.bottom_row()
        if caret_row < top_row + 1 or caret_row > bottom_row - 1:
            self.view.run_command("show_at_center")
