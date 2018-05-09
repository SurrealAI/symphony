import os
from symphony.spec import ProcessSpec
from symphony.utils.common import print_err
from .common import tmux_name_check


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
        if cmds is None:
            cmds = []
        self.start_dir = os.path.expanduser(start_dir or '.')
        if not isinstance(cmds, (tuple, list)):
            print_err(
                '[Warning] command "{}" for TmuxProcess "{}" should be a list'
                .format(cmds, name))
            self.cmds = [cmds]
        else:
            self.cmds = list(cmds)
        self.env = {}

    def set_envs(self, di):
        """
        Set environment variables
        Args:
            di(env_var_name(str): env_var_val(str))
        """
        for k, v in di.items():
            self.env[k] = v

    @classmethod
    def load_dict(cls):
        pass

    def dump_dict(self):
        pass
