import os
import time
import libtmux
from libtmux.exc import LibTmuxException
from symphony.engine import Cluster
from symphony.tmux.experiment import TmuxExperimentSpec
from symphony.errors import *


_SERVER_NAME = 'default'
_DEFAULT_WINDOW = '__main__'


def _logger(verbose):
    def _log(*args, **kwargs):
        if verbose:
            print(*args, **kwargs)
    return _log


class TmuxCluster(Cluster):
    def __init__(self, server_name=None):
        """
        Args:
            server_name: name of the new Tmux server (i.e. socket_name)
        """
        super().__init__() # just for linter's happiness
        self._socket_name = server_name or _SERVER_NAME
        # Use /dev/null as config to ignore all user-specific settings.
        self._tmux = libtmux.Server(socket_name=self._socket_name,
                                    config_file='/dev/null')

    # =================== Private helpers ====================
    def _get_session(self, session_name):
        try:
            sess = self._tmux.find_where({'session_name': session_name})
        except LibTmuxException:
            raise ValueError('Experiment "{}" does not exist'.format(session_name))
        if not sess:
            raise ValueError('Experiment "{}" does not exist'.format(session_name))
        return sess

    def _get_window_name(self, process_name, group_name):
        if group_name:
            window_name = ':'.join((group_name, process_name))
        else:
            window_name = process_name
        return window_name

    def _get_window(self, session_name, process_name, group_name=None):
        sess = self._get_session(session_name)
        window_name = self._get_window_name(process_name, group_name)
        window = sess.find_where({'window_name': window_name})
        if not window:
            raise ValueError('Process "{}" does not exist'.format(window_name))
        return window

    def _new_session(self, session_name):
        try:
            if self._tmux.has_session(session_name):
                raise ResourceExistsError(
                        'Experiment "{}" already exists'.format(session_name))
        except LibTmuxException:
            pass
        return self._tmux.new_session(session_name)

    def _create_process(self, sess, process, preamble_cmds, process_group=None,
                        timeout=4):
        if process_group:
            window_name = ':'.join((process_group.name, process.name))
        else:
            window_name = process.name
        window = sess.new_window(window_name=window_name)

        # Retry loop to make sure we run process commands after
        # shell starts (heuristically checked by ensuring pane has
        # some output in the buffer).
        env_cmds = ['export {}={}'.format(k,v) for k,v in process.env.items()]
        cmds = env_cmds + preamble_cmds + process.cmds
        if cmds:
            start_time = time.time()
            pane = window.attached_pane
            while time.time() < start_time + timeout:
                stdout = pane.cmd('capture-pane', '-p').stdout
                if stdout:
                    for cmd in cmds:
                        pane.send_keys(cmd)
                    break
                time.sleep(0.2)

    def _send_cmd(self, experiment_name, process, process_group_name=None):
        window = self._get_window(experiment_name, process.name,
                                  group_name=process_group_name)
        pane = window.attached_pane
        if process.cmds:
            for cmd in process.cmds:
                pane.send_keys(cmd)

    # ===================== Launch API =======================
    def new_experiment(self, *args, **kwargs):
        return TmuxExperimentSpec(*args, **kwargs)

    def launch(self, spec, dry_run=False):
        _log = _logger(dry_run)
        assert isinstance(spec, TmuxExperimentSpec)

        spec.compile()

        # Create a new session for the given Experiment.
        if not dry_run:
            sess = self._new_session(spec.name)
            # Change the name of the default window.
            sess.windows[0].rename_window(_DEFAULT_WINDOW)
        _log('Creating new Experiment "{}"'.format(spec.name))

        # Create a window for each process group and lone process.
        for pg in spec.list_process_groups():
            preamble_cmds = spec.preamble_cmds + pg.preamble_cmds
            _log(' --> Creating process group', pg.name)
            for p in pg.list_processes():
                window_name = ':'.join((pg.name, p.name))
                if not dry_run:
                    self._create_process(sess, p, preamble_cmds,
                                         process_group=pg)
                _log(' --> --> Created process', window_name)

        for p in spec.list_processes():
            if not dry_run:
                self._create_process(sess, p, spec.preamble_cmds)
            _log(' --> Created process', p.name)

    def launch_batch(self, experiment_specs):
        for exp in experiment_specs:
            self.launch(exp)

    # ===================== Action API =======================
    def delete(self, experiment_name):
        sess = self._get_session(experiment_name)
        sess.kill_session()

    def delete_batch(self, experiments):
        for exp in experiments:
            self.delete(exp)

    def transfer_file(self, experiment_name, src, dest):
        """
        scp for remote backends
        """
        # TODO
        raise NotImplementedError

    def login(self, experiment_name, *args, **kwargs):
        """
        ssh for remote backends
        """
        # TODO
        # tmux -L <server> select-window -t <session>:<window>; a -t <session>
        raise NotImplementedError

    def exec_command(self, experiment_name, command, *args, **kwargs):
        """
        command(array(string))
        """
        # XXX
        raise NotImplementedError

    # ===================== Query API ========================
    def list_experiments(self):
        """
        Returns:
            list of experiment names
        """
        try:
            return [sess.name for sess in self._tmux.sessions]
        except LibTmuxException:
            return []

    def fuzzy_match_experiments(self):
        # TODO
        pass

    def describe_experiment(self, experiment_name):
        """
        Returns:
        {
            'pgroup1': {
                'p1': {'status': 'live', 'timestamp': '11:23'},
                'p2': {'status': 'dead'}
            },
            None: {  # always have all the processes
                'p3_lone': {'status': 'running'}
            }
        }
        """
        sess = self._get_session(experiment_name)
        result = dict()
        for window in sess.windows:
            if window.name == _DEFAULT_WINDOW:
                continue
            tokens = window.name.split(':')
            if len(tokens) == 1:
                group, process = None, tokens[0]
            else:
                group, process = tokens[0], tokens[1]
            result[group] = result.get(group, dict())
            # TODO: Add other attributes available from tmux
            result[group][process] = {
                    'status': 'live',
            }
        return result

    def describe_process_group(self,
                               experiment_name,
                               process_group_name):
        """
        Returns:
        {
            'p1': {'status': 'live', 'timestamp': '11:23'},
            'p2': {'status': 'dead'}
        }
        """
        return self.describe_experiment(experiment_name)[process_group_name]

    def describe_process(self,
                         experiment_name,
                         process_name,
                         process_group_name=None):
        """
        Returns:
            {'status: 'live', 'timestamp': '23:34'}
        """
        window = self._get_window(
                experiment_name, process_name, group_name=process_group_name)
        # TODO: Add other attributes available from tmux
        return {
                'status': 'live',
        }

    def get_log(self, experiment_name, process_name, process_group=None,
                follow=False, since=None, tail=None, print_logs=False):
        if follow:
            raise ValueError(
                    '[Error] "follow" is not supported for tmux backend')
        if since:
            raise ValueError(
                    '[Error] "since" is not supported for tmux backend')
        window = self._get_window(
                experiment_name, process_name, group_name=process_group)
        pane = window.attached_pane
        command = ['capture-pane', '-p']
        if tail:
            command.extend(['-S', str(-abs(tail))])
        stdout = pane.cmd(*command).stdout
        if print_logs:
            print('\n'.join(stdout))
        return stdout
