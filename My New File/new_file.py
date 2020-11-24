# Save a new file to the current folder by default

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
