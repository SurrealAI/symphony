from .base import BaseSpec
from .process import ProcessSpec
from .process_group import ProcessGroupSpec
from symphony.engine.application_config import SymphonyConfig
# from symphony.utils.common import 


class ExperimentSpec(BaseSpec):
    def __init__(self, name, use_global_name_prefix=True):
        if use_global_name_prefix and SymphonyConfig().experiment_name_prefix:
            if name.find(SymphonyConfig().experiment_name_prefix) != 0:
                name = SymphonyConfig().experiment_name_prefix + '-' + name
        super().__init__(name)
        self.lone_processes = {}
        self.all_processes = {}
        self.process_groups = {}
        
    def add_process_group(self, process_group):
        assert isinstance(process_group, ProcessGroupSpec)
        process_group_name = process_group.name
        if process_group_name in self.process_groups:
            raise ValueError('[Error] Cannot add process group {} to experiment \
                {}: a process group with the same name already exists'.format(process_group_name, self.name))
        self.process_groups[process_group_name] = process_group
        process_group._set_experiment(self)

    def add_process_groups(self, process_groups):
        for pg in process_groups:
            self.add_process_group(pg)

    def new_process_group(self, *args, **kwargs):
        """
        Call self.add_process_group

        Returns:
            new ProcessGroupSpec
        """
        pg = self._new_process_group(*args, **kwargs)
        self.add_process_group(pg)
        return pg

    def _new_process_group(self, *args, **kwargs):
        raise NotImplementedError

    def get_process_group(self, name):
        return self.process_groups[name]

    def list_process_groups(self):
        return self.process_groups.values()

    def add_process(self, process, lone=True):
        assert isinstance(process, ProcessSpec)
        process_name = process.name
        if process_name in self.all_processes:
            raise ValueError('[Error] Cannot add process {} to experiment \
            {}: a process with the same name already exists'.format(process_name, self.name))
        if lone:
            self.lone_processes[process_name] = process
        self.all_processes[process_name] = process
        process._set_experiment(self)

    def add_processes(self, processes):
        for p in processes:
            self.add_process(p)

    def new_process(self, *args, **kwargs):
        """
        Returns:
            new ProcessSpec
        """
        p = self._new_process(*args, **kwargs)
        self.add_process(p)
        return p

    def _new_process(self, *args, **kwargs):
        raise NotImplementedError

    def get_process(self, name):
        return self.lone_processes[name]

    def list_processes(self):
        return self.lone_processes.values()

    @classmethod
    def from_dict(cls):
        raise NotImplementedError

    def to_dict(self):
        raise NotImplementedError
