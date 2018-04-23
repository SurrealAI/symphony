from .base import BaseSpec
from .process import ProcessSpec
from .process_group import ProcessGroupSpec


class ExperimentSpec(BaseSpec):
    def __init__(self, name):
        super().__init__(name)
        self.lone_processes = {}
        self.process_groups = {}

    def add_process_group(self, process_group):
        assert isinstance(process_group, ProcessGroupSpec)
        self.process_groups[process_group.name] = process_group
        process_group.parent_experiment = self

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

    def all_process_groups(self):
        return self.process_groups.values()

    def add_lone_process(self, process):
        assert isinstance(process, ProcessSpec)
        self.lone_processes[process.name] = process
        process.parent_experiment = self

    def add_lone_processes(self, processes):
        for p in processes:
            self.add_lone_process(p)

    def new_lone_process(self, *args, **kwargs):
        """
        Returns:
            new ProcessSpec
        """
        p = self._new_lone_process(*args, **kwargs)
        self.add_lone_process(p)
        return p

    def _new_lone_process(self, *args, **kwargs):
        raise NotImplementedError

    def all_lone_processes(self):
        return self.lone_processes.values()

    @classmethod
    def from_dict(cls):
        raise NotImplementedError

    def to_dict(self):
        raise NotImplementedError
