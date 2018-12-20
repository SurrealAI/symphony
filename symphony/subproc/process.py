import os
from symphony.spec import ProcessSpec


class SubprocProcessSpec(ProcessSpec):
    def __init__(self, name, cmd):
        """
        Args:
            name: name of the process
            cmd: string command
        """
        super().__init__(name)
        self.cmd = cmd
        self.env = {}

    def set_envs(self, env):
        """
        Set environment variables
        Args:
            env: dict
        """
        self.env.update(env)

    def _load_dict(self, di):
        super()._load_dict(di)
        self.cmd = di['cmd']

    def dump_dict(self):
        di = super().dump_dict()
        di['cmd'] = self.cmd
        return di
