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
