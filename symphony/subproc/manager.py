"""
Manages subprocesses launching and polling
"""
import os
import subprocess
import time
import signal
import sys


class SubprocManager:
    def __init__(self,
                 stdout_mode='print',
                 stderr_mode='print',
                 log_dir=None):
        """
        Args:
            stdout_mode: ['print', 'file', 'none']
            stderr_mode: ['print', 'file', 'none', 'stdout']
            log_dir: where stdout is saved as <name>.out and stderr as <name>.err
              if either stdout or stderr mode is file, log_dir cannot be None
        """
        self.stdout_mode = stdout_mode.lower()
        self.stderr_mode = stderr_mode.lower()
        assert self.stdout_mode in ['print', 'file', 'none']
        assert self.stderr_mode in ['print', 'file', 'none', 'stdout']
        self.processes = {}  # {"name": Popen}
        if stdout_mode == 'file' or stderr_mode == 'file':
            assert log_dir is not None
            self.log_dir = os.path.expanduser(log_dir)
            os.makedirs(self.log_dir, exist_ok=True)
        else:
            self.log_dir = None

    def launch(self, name, cmd, env):
        """
        Args:
            name: process name
            cmd: shell command
            env (dict): environment variables

        Returns:
            Popen
        """
        assert name not in self.processes, 'process "{}" already exists'.format(name)
        if self.stdout_mode == 'file':
            stdout = open(os.path.join(self.log_dir, name+'.out'), 'w')
        elif self.stdout_mode == 'print':
            stdout = None
        else:
            stdout = subprocess.DEVNULL

        if self.stderr_mode == 'file':
            stderr = open(os.path.join(self.log_dir, name+'.err'), 'w')
        elif self.stderr_mode == 'print':
            stderr = None
        elif self.stderr_mode == 'stdout':
            stderr = subprocess.STDOUT
        else:
            stderr = subprocess.DEVNULL

        # environment will inherit from parent process
        assert isinstance(env, dict)
        for key, value in env.items():
            if not isinstance(value, str):
                env[key] = str(value)
        env.update(os.environ)

        proc = subprocess.Popen(
            cmd,
            executable='/bin/bash',
            shell=True,
            bufsize=1,  # line buffered
            universal_newlines=True,  # force text stream
            stdout=stdout,
            stderr=stderr,
            env=env
        )
        self.processes[name] = proc
        return proc

    def poll(self, name):
        """
        Returns:
        - 0: process finishes without error
        - non-zero: process finishes with error
        - None: process still running
        """
        assert name in self.processes, 'process "{}" does not exist'.format(name)
        return self.processes[name].poll()

    def poll_all(self):
        return {name: self.poll(name) for name in self.processes}

    def kill(self, name, verbose=False):
        if self.poll(name) is None:
            proc = self.processes[name]
            proc.kill()
            if verbose:
                print('KILLED', proc.pid)

    def kill_all(self, verbose=False):
        for name in self.processes:
            self.kill(name, verbose=verbose)

    SIG_DICT = {
        signal.SIGINT : 'SIGINT',
        signal.SIGTERM : 'SIGTERM',
        signal.SIGABRT : 'SIGABRT',
        signal.SIGILL : 'SIGILL',
        signal.SIGFPE : 'SIGFPE',
        signal.SIGSEGV : 'SIGSEGV',
        signal.SIGQUIT : 'SIGQUIT',
        signal.SIGHUP : 'SIGHUP',
    }

    def _signal_handler(self, sig, frame):
        signame = self.SIG_DICT[sig]
        print(signame + ' RECEIVED, KILLING ALL REMAINING PROCESSES ...')
        self.kill_all(verbose=True)
        sys.exit(0)

    def join(self, kill_on_error=True, poll_interval=1.0):
        """
        Wait for all processes to finish.
        
        Args:
            kill_on_error: True to kill all processes if any of them returns
                non-zero code.
            poll_interval: seconds between polling
        """
        for sig in self.SIG_DICT:
            signal.signal(sig, self._signal_handler)
        remaining_procs = list(self.processes.keys())
        while remaining_procs:
            for name in remaining_procs[:]:
                proc = self.processes[name]
                retcode = proc.poll()
                if retcode is None:  # process still running normally
                    continue
                else:
                    remaining_procs.remove(name)
                    if retcode == 0:
                        print('PROCESS "{}" DONE'.format(name))
                    else:
                        print('PROCESS "{}" TERMINATED WITH ERROR CODE {}'
                              .format(name, retcode))
                        if kill_on_error:
                            print('KILLING ALL REMAINING PROCEESES ...')
                            self.kill_all(verbose=True)
                            remaining_procs = []
                            break
            time.sleep(poll_interval)
