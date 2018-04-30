from symphony.spec import ProcessSpec
from .common import *


class TmuxProcessSpec(ProcessSpec):
    def __init__(self, name, cmds=None, start_dir=None):
        """
        Args:
            name: name of the process
            cmds: list of commands to run
            start_dir: directory in which the process starts
        """
        tmux_name_check(name, 'Process')
        super().__init__(name)
        self.start_dir = os.path.expanduser(start_dir)
        self.cmds = cmds

    @classmethod
    def load_dict(cls):
        pass

    def dump_dict(self):
        pass
