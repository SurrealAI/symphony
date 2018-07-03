from benedict import BeneDict
from symphony.spec import ProcessGroupSpec
from symphony.utils.common import check_valid_hostname
from symphony.utils.common import get_grouped_docker_process_name
from .process import DockerProcessSpec


class DockerProcessGroupSpec(ProcessGroupSpec):
    _ProcessClass = DockerProcessSpec

    def __init__(self, group_name):
        check_valid_hostname(group_name)
        super().__init__(group_name)
        self.group_name = group_name

    def _load_dict(self, di):
        self.group_name = di['group_name']
        super()._load_dict(di)

    def dump_dict(self):
        di = super().dump_dict()
        di['group_name'] = self.group_name
        return di

    def yml_dict(self):
        proc_dict = BeneDict()
        for p in self.list_processes():
            name = get_grouped_docker_process_name(self.group_name, p.name)
            proc_dict[name] = p.service_yml.data
        return proc_dict

    def yml(self):
        return self.yml_dict().dump_yaml_str()

    def set_env(self, name, value):
        for process in self.list_processes():
            process.set_env(name, value)

    def set_envs(self, di):
        for process in self.list_processes():
            process.set_envs(di)
