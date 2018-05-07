from symphony.engine.application_config import SymphonyConfig
from symphony.engine.address_book import AddressBook
from .base import BaseSpec
from .process import ProcessSpec
from .process_group import ProcessGroupSpec


class ExperimentSpec(BaseSpec):
    _ProcessClass = None
    _ProcessGroupClass = None

    def __init__(self, name):
        if SymphonyConfig().username:
            if name.find(SymphonyConfig().username) != 0:
                name = SymphonyConfig().username + '-' + name
        super().__init__(name)
        self.address_book = AddressBook()
        self.lone_processes = {}
        self.all_processes = {}
        self.process_groups = {}

    def add_process_group(self, process_group):
        assert isinstance(process_group, ProcessGroupSpec)
        process_group_name = process_group.name
        if process_group_name in self.process_groups:
            raise ValueError('[Error] Cannot add process group {} to experiment \
                {}: a process group with the same name already exists' \
                .format(process_group_name, self.name))
        self.process_groups[process_group_name] = process_group
        process_group._set_experiment(self)

    def add_process_groups(self, process_groups):
        for process_group in process_groups:
            self.add_process_group(process_group)

    def new_process_group(self, *args, **kwargs):
        """
        Call self.add_process_group

        Returns:
            new ProcessGroupSpec
        """
        if self._ProcessGroupClass is None:
            raise NotImplementedError('please define class variable _ProcessGroupClass')
        process_group = self._ProcessGroupClass(*args, **kwargs)
        self.add_process_group(process_group)
        return process_group

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
        for process in processes:
            self.add_process(process)

    def new_process(self, *args, **kwargs):
        """
        Returns:
            new ProcessSpec
        """
        process = self._ProcessClass(*args, **kwargs)
        self.add_process(process)
        return process

    def get_process(self, name):
        return self.lone_processes[name]

    def list_processes(self):
        return self.lone_processes.values()

    def list_all_processes(self):
        return self.all_processes.values()

    @classmethod
    def load_dict(cls, di):
        name = di['name']
        instance = cls(name)
        instance._load_dict(di)
        return instance

    def _load_dict(self, data):
        pgs = data['process_groups']
        for dictionary in pgs:
            self.add_process_group(self._ProcessGroupClass.load_dict(dictionary))
        processes = data['processes']
        for dictionary in processes:
            self.add_process(self._ProcessClass.load_dict(dictionary))
        self.address_book = AddressBook(data['ab'])

    def dump_dict(self):
        pgs = []
        for process_group in self.list_process_groups():
            pgs.append(process_group.dump_dict())
        pcs = []
        for process in self.list_processes():
            pcs.append(process.dump_dict())
        return {'process_groups': pgs,
                'processes': pcs,
                'name': self.name,
                'ab': self.address_book.entries,
               }
