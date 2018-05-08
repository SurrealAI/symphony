import os

from symphony.spec import ProcessSpec
from .common import *


class TmuxProcessSpec(ProcessSpec):
    def __init__(self, name, cmds=[], start_dir=None):
        """
        Args:
            name: name of the process
            cmds: list of commands to run
            start_dir: directory in which the process starts
        """
        tmux_name_check(name, 'Process')
        super().__init__(name)
        self.start_dir = os.path.expanduser(start_dir or '.')
        if not isinstance(cmds, (tuple, list)):
            self.cmds = [cmds]
        else:
            self.cmds = list(cmds)
        self.cmds = cmds

    @classmethod
    def load_dict(cls):
        pass

    def dump_dict(self):
        pass
