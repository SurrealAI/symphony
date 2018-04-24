import os
import libtmux
from symphony.engine import Cluster
from symphony.tmux.experiment import TmuxExperimentSpec
from symphony.errors import *


_SERVER_NAME = '__symphony__'
_DEFAULT_WINDOW = '__main__'


class TmuxCluster(Cluster):
    def __init__(self, start_dir='~', preamble_cmd=None,
                 dry_run=False):
        """
        Args:
          start_dir: root directory in which the Tmux session starts
          preamble_cmd: str or list of str containing command(s) to run in each
              process before the actual command (e.g. `source activate py3`)
          dry_run: if True, do not create a Tmux session and only show what
              would be done
        """
        self._start_dir = os.path.expanduser(start_dir)
        self._preamble_cmd = preamble_cmd
        self._dry_run = dry_run
        self._socket_name = _SERVER_NAME
        self._tmux = libtmux.Server(socket_name=self._socket_name)

    # =================== Private helpers ====================
    def _session(self, name):
        return self._tmux.find_where({'session_name': name})

    # ===================== Launch API =======================
    def new_experiment(self, *args, **kwargs):
        return TmuxExperimentSpec(*args, **kwargs)

    def launch(self, spec):
        assert isinstance(spec, TmuxExperimentSpec)
        print('Attempting to launch', spec.name)
        for pg in spec.list_process_groups():
            print(' -->', pg.name)
            for p in pg.list_processes():
                print('  ---->', p.name)
        print('\n===================\n')
        if self._tmux.has_session(spec.name):
            raise ResourceExistsError(
                    'Experiment "{}" already exists'.format(spec.name))
        self._tmux.new_session(spec.name)

    def launch_batch(self, experiment_specs):
        for exp in experiment_specs:
            self.launch(exp)

    # ===================== Action API =======================
    def delete(self, experiment):
        if self._tmux.has_session(experiment):
            self._tmux.kill_session(experiment)
        else:
            raise ValueError('Experiment {} does not exist'.format(experiment))

    def delete_batch(self, experiments):
        for exp in experiments:
            self.delete(exp)

    def transfer_file(self, src, dest):
        """
        scp for remote backends
        """
        raise NotImplementedError

    def login(self, *args, **kwargs):
        """
        ssh for remote backends
        """
        raise NotImplementedError

    def exec_command(self, *args, **kwargs):
        raise NotImplementedError

    # ===================== Query API ========================
    def list_experiments(self):
        return [sess.name for sess in self._tmux.sessions]

    def fuzzy_match_experiments(self):
        # TODO
        pass

    def list_process_groups(self, experiment):
        if self._tmux.has_session(experiment):
            return [w.name for w in self._session(experiment).windows]
        else:
            raise ValueError('Experiment {} does not exist'.format(experiment))

    def list_processes(self, experiment, process_group=None):
        sess = self._session(experiment)
        if not sess:
            raise ValueError('Experiment {} does not exist'.format(experiment))

        if process_group:
            groups = [process_group]
        else:
            groups = self.list_process_groups(experiment)

        processes = []
        for pg in groups:
            window = sess.find_where({'window_name': pg})
            if pg:
                processes.extend([p.name for p in pg])
        return processes

    def status(self, experiment, process, process_group=None):
        raise NotImplementedError

    def get_stdout(self, experiment, process, process_group=None):
        # XXX
        """
        Args:
            history: number of lines before the visible pane to be captured.
        """
        window = self.get_window(session_name, window_name)

        if window is None:
            raise ValueError('window "{}" does not exist'.format(window_name))
        pane = window.attached_pane
        cmd = ['capture-pane', '-p']
        if history != 0:
            cmd += ['-S', str(-abs(history))]
        return pane.cmd(*cmd).stdout

    def get_stderr(self, experiment, process, process_group=None):
        raise NotImplementedError
