import os

from symphony.spec import ProcessGroupSpec
from symphony.utils.common import print_err
from .common import tmux_name_check
from .process import TmuxProcessSpec


class TmuxProcessGroupSpec(ProcessGroupSpec):
    _ProcessClass = TmuxProcessSpec

    def __init__(self, name, start_dir=None, preamble_cmds=None):
        """
        Args:
            name: name of the Experiment
            start_dir: directory where new processes start for this Experiment
            preamble_cmds: str or list of str containing commands to run in each
                process before the actual command (e.g. `source activate py3`)
        """
        tmux_name_check(name, 'ProcessGroup')
        super().__init__(name)
        self.start_dir = os.path.expanduser(start_dir or '.')
        if preamble_cmds is None:
            preamble_cmds = []
        if not isinstance(preamble_cmds, (tuple, list)):
            self.preamble_cmds = [preamble_cmds]
            print_err(('[Warning] preamble command "{}" for TmuxProcessGroup ' +
                       '"{}" should be a list').format(preamble_cmds, name))
        else:
            self.preamble_cmds = list(preamble_cmds)

    def _new_process(self, *args, **kwargs):
        return TmuxProcessSpec(*args, **kwargs)

    def _load_dict(self, di):
        super()._load_dict(di)
        self.start_dir = di['start_dir']
        self.preamble_cmds = di['preamble_cmds']

    def dump_dict(self):
        di = super().dump_dict()
        di['start_dir'] = self.start_dir
        di['preamble_cmds'] = self.preamble_cmds
        return di
