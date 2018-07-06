import copy
from benedict import BeneDict
from symphony.spec import ExperimentSpec
from symphony.engine.address_book import AddressBook
from symphony.utils.common import compact_range_dumps, compact_range_loads
from symphony.utils.common import check_valid_project_name
from .process import DockerProcessSpec
from .process_group import DockerProcessGroupSpec


class DockerExperimentSpec(ExperimentSpec):
    _ProcessClass = DockerProcessSpec
    _ProcessGroupClass = DockerProcessGroupSpec

    def __init__(self, name, port_range=None):
        check_valid_project_name(name)
        super().__init__(name)

    def _load_dict(self, di):
        super()._load_dict(di)

    def dump_dict(self):
        data = super().dump_dict()
        return data

    def yml(self):
        di = BeneDict({
            'version': '3',
        })
        for pg in self.list_process_groups():
            if 'services' not in di:
                di['services'] = {}
            di['services'].update(pg.yml_dict())
        for p in self.list_processes():
            di['services'][p.name] = p.yml_dict()
        return di.dump_yaml_str()

