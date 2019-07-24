from mixins import AutoReload
from repository.base_repository import BaseRepository
from watchdog.observers import Observer
from watchdog.events import RegexMatchingEventHandler
import os.path

"""
    Watches the config directory for any changes to python files
    If it finds a change, rewrites all existing Config instances with new data
"""


class Watchdog(BaseRepository, RegexMatchingEventHandler):

    def __init__(self):
        super().__init__()
        RegexMatchingEventHandler.__init__(self, regexes=[r'.*[.]py$'],
                                           ignore_directories=True)

        self.observer = Observer()
        self.observer.schedule(self, '.', recursive=True)
        self.observer.start()

    def __del__(self):
        self.observer.stop()
        self.observer.join()

    def on_modified(self, event):
        print("Reloading {}".format(event.src_path))
        AutoReload.reload(os.path.abspath(event.src_path))
