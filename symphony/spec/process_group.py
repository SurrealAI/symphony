from .base import BaseSpec
from .process import ProcessSpec


class ProcessGroupSpec(BaseSpec):
    _ProcessClass = None

    def __init__(self, name):
        super().__init__(name)
        self.processes = {}
        self.parent_experiment = None

    def add_process(self, process):
        """Inserts a process to this process group
        Args:
            process(ProcessSpec): Process to be added
        """
        assert isinstance(process, ProcessSpec)
        self.processes[process.name] = process
        process._set_process_group(self)
        if self.parent_experiment is not None:
            self.parent_experiment.add_process(process, lone=False)

    def _set_experiment(self, experiment):
        """ Internal method
            Set process group to belong to experiment
        """
        if self.parent_experiment is not None:
            raise ValueError('[Error] Process group {} cannot be added to experiment {}. \
                It is already in experiment {}'.format(self.name,
                                                       experiment.name,
                                                       self.parent_experiment.name))
        self.parent_experiment = experiment
        for process in self.processes.values():
            experiment.add_process(process, lone=False)

    def get_process(self, name):
        return self.processes[name]

    def add_processes(self, processes):
        for p in processes:
            self.add_process(p)

    def new_process(self, *args, **kwargs):
        """
        Returns:
            new ProcessSpec
        """
        if self._ProcessClass is None:
            raise NotImplementedError('Please define class variable _ProcessClass')
        process = self._ProcessClass(*args, **kwargs)
        self.add_process(process)
        return process

    def list_processes(self):
        return self.processes.values()

    @classmethod
    def load_dict(cls, data):
        instance = cls(data['name'])
        instance._load_dict(data)
        return instance

    def _load_dict(self, data):
        processes = data['processes']
        for dictionary in processes:
            self.add_process(self._ProcessClass.load_dict(dictionary))

    def dump_dict(self):
        processes = []
        for process in self.list_processes():
            processes.append(process.dump_dict())
        return {'processes': processes, 'name': self.name}
