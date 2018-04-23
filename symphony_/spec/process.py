from .base import BaseSpec


class ProcessSpec(BaseSpec):
    def __init__(self, name):
        super().__init__(name)
        self.parent_process_group = None
        self.parent_experiment = None

    def binds(self, address):
        pass

    def connects(self, address):
        pass

    def exposes(self, address):
        pass

    @classmethod
    def from_dict(cls):
        raise NotImplementedError

    def to_dict(self):
        raise NotImplementedError
