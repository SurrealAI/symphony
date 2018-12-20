import os
import time
import shlex
from .experiment import SubprocExperimentSpec
from .manager import SubprocManager
from symphony.engine import Cluster
from symphony.errors import *


def _logger(verbose):
    def _log(*args, **kwargs):
        if verbose:
            print(*args, **kwargs)
    return _log


class SubprocCluster(Cluster):
    def __init__(self,
                 stdout_mode='print',
                 stderr_mode='print',
                 log_dir=None,
                 ):
        """
        Args:
            stdout_mode: ['print', 'file', 'none']
            stderr_mode: ['print', 'file', 'none', 'stdout']
            log_dir: where stdout is saved as <name>.out and stderr as <name>.err
              if either stdout or stderr mode is file, log_dir cannot be None
        """
        super().__init__()  # just for linter's happiness
        self._manager = SubprocManager(
            stdout_mode=stdout_mode,
            stderr_mode=stderr_mode,
            log_dir=log_dir
        )

    # =================== Private helpers ====================
    def _launch_process(self, name, p, dry_run):
        if dry_run:
            print(p.cmd, '; ENV=', p.env)
        else:
            self._manager.launch(name, p.cmd, p.env)

    def _join(self):
        self._manager.join(kill_on_error=True)

    # ===================== Launch API =======================
    def new_experiment(self, *args, **kwargs):
        return SubprocExperimentSpec(*args, **kwargs)

    def launch(self, spec, dry_run=False, verbose=True):
        _log = _logger(verbose)
        assert isinstance(spec, SubprocExperimentSpec)

        spec.compile()

        _log('Creating new Experiment "{}"'.format(spec.name))

        for pg in spec.list_process_groups():
            _log(' --> Creating process group', pg.name)
            for p in pg.list_processes():
                name = pg.name + ':' + p.name
                self._launch_process(name, p, dry_run=dry_run)
                _log(' --> --> Created process', name)

        for p in spec.list_processes():
            self._launch_process(p.name, p, dry_run=dry_run)
            _log(' --> Created process', p.name)

        self._join()
