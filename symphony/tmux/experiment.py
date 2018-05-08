import os
from symphony.spec import ExperimentSpec
from symphony.utils.common import print_err
from .common import tmux_name_check
from .process import TmuxProcessSpec
from .process_group import TmuxProcessGroupSpec


class TmuxExperimentSpec(ExperimentSpec):
    _ProcessClass = TmuxProcessSpec
    _ProcessGroupClass = TmuxProcessGroupSpec

    def __init__(self, name, start_dir=None, preamble_cmds=[]):
        """
        Args:
            name: name of the Experiment
            start_dir: directory where new processes start for this Experiment
            preamble_cmds: str or list of str containing commands to run in each
                process before the actual command (e.g. `source activate py3`)
        """
        # Valid session name is not empty and doesn't contain colon or period.
        # (reference: https://github.com/tmux/tmux/blob/master/session.c)
        tmux_name_check(name, 'Experiment')
        super().__init__(name)
        self.start_dir = os.path.expanduser(start_dir or '.')
        if not isinstance(preamble_cmds, (tuple, list)):
            self.preamble_cmds = [preamble_cmds]
            print_err(('[Warning] preamble command "{}" for TmuxExperiment ' +
                       '"{}" should be a list').format(preamble_cmds, name))
        else:
            self.preamble_cmds = list(preamble_cmds)

    def _new_process(self, *args, **kwargs):
        return TmuxProcessSpec(*args, **kwargs)

    def _new_process_group(self, *args, **kwargs):
        return TmuxProcessGroupSpec(*args, **kwargs)

    @classmethod
    def load_dict(cls):
        pass

    def dump_dict(self):
        pass
