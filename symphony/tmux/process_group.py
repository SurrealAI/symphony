from symphony.spec import ProcessGroupSpec
from .process import TmuxProcessSpec
from .common import *


class TmuxProcessGroupSpec(ProcessGroupSpec):
    def __init__(self, name, start_dir=None, preamble_cmd=None):
        """
        Args:
            name: name of the Experiment
            start_dir: directory where new processes start for this Experiment
            preamble_cmd: str or list of str containing commands to run in each
                process before the actual command (e.g. `source activate py3`)
        """
        tmux_name_check(name, 'ProcessGroup')
        super().__init__(name)
        self.start_dir = start_dir
        if preamble_cmd and type(preamble_cmd) != list:
            self.preamble_cmd = [preamble_cmd]
        else:
            self.preamble_cmd = preamble_cmd

    def _new_process(self, *args, **kwargs):
        return TmuxProcessSpec(*args, **kwargs)

    @classmethod
    def load_dict(cls):
        pass

    def dump_dict(self):
        pass
