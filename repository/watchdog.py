from importlib import reload
from config import config
from repository.base_repository import BaseRepository
from watchdog.observers import Observer
from watchdog.events import RegexMatchingEventHandler

"""
    Watches the config directory for any changes to python files
    If it finds a change, rewrites all existing Config instances with new data
"""


class Watchdog(BaseRepository, RegexMatchingEventHandler):

    def __init__(self):
        super().__init__()
        RegexMatchingEventHandler.__init__(self, regexes=[r'.*/config[.]py$'],
                                           ignore_directories=True)
        self.observer = Observer()
        self.observer.schedule(self, './config', recursive=True)
        self.observer.start()

    def __del__(self):
        self.observer.stop()
        self.observer.join()

    def on_modified(self, event):
        """
            Move the instance list from old config to new reloaded config,
            so we can reload all instances with new data
        """
        config_instances = config.Config.get_instances()
        print("Reloading {} config instances".format(len(config_instances)))
        reload(config)
        config.Config.set_instances(config_instances)
        config.Config.update_all(config.Config())
