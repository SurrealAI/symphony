"""
All experiments, processes, and process_groups extend from this base class
"""
from benedict import BeneDict


class BaseSpec:
    def __init__(self, name):
        self.name = name

    def to_dict(self):
        raise NotImplementedError

    @classmethod
    def from_dict(cls):
        raise NotImplementedError

    def to_json_str(self):
        # TODO taken care of in BeneDict
        pass

    @classmethod
    def from_json_str(cls, string):
        # TODO taken care of in BeneDict
        pass

    def to_json_file(self, file_path):
        # TODO taken care of in BeneDict
        pass

    @classmethod
    def from_json_file(cls, file_path):
        # TODO taken care of in BeneDict
        pass

    def to_yaml_str(self):
        # TODO taken care of in BeneDict
        pass

    @classmethod
    def from_yaml_str(cls, string):
        # TODO taken care of in BeneDict
        pass

    def to_yaml_file(self, file_path):
        # TODO taken care of in BeneDict
        pass

    @classmethod
    def from_yaml_file(cls, file_path):
        # TODO taken care of in BeneDict
        pass
