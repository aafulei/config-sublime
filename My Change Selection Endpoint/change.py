# https://forum.sublimetext.com/t/move-caret-to-beginning-or-end-of-selection-without-losing-selection/29329/2

# OdatNurd

# import sublime
# import sublime_plugin

# class ChangeSelectionEndpointCommand(sublime_plugin.TextCommand):
#     def run(self, edit):
#         new_sel = []
#         for sel in self.view.sel():
#             # reverse = (sel.a < sel.b) if begin else (sel.b < sel.a)
#             reverse = True
#             new_sel.append(sublime.Region(sel.b, sel.a) if reverse else sel)
#         self.view.sel().clear()
#         self.view.sel().add_all(new_sel)
