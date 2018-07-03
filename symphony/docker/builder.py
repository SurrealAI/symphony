import copy
from symphony.utils.common import merge_dict, strip_repository_name
from symphony.utils.common import get_grouped_docker_process_name
from benedict import BeneDict


class DockerConfigYML(object):
    def __init__(self):
        self.data = BeneDict({})

    def yml(self):
        """
        Dump yml string for Docker Compose configuration.
        """
        raise NotImplementedError


class DockerServiceYML(DockerConfigYML):
    def __init__(self, name, container_image):
        super().__init__()
        self.name = name
        self.data = BeneDict({
            'image': container_image,
        })

    @classmethod
    def load(cls, di):
        name = di['name']
        data = di['data']
        container_image = data['image']
        instance = cls(name, container_image)
        instance.data = BeneDict(di['data'])
        return instance

    def save(self):
        di = {}
        di['name'] = self.name
        di['data'] = self.data
        return di

    def yml(self):
        return self.data.dump_yaml_str()

    def set_env(self, name, value):
        if 'environment' not in self.data.keys():
            self.data['environment'] = BeneDict()
        self.data['environment'][name] = value

    def set_envs(self, di):
        for k, v in di.items():
            self.set_env(k, v)

    def set_hostname(self, hostname):
        self.data.hostname = hostname

    def set_port(self, port):
        if 'ports' not in self.data.keys():
            self.data['ports'] = []
        self.data['ports'].append(port)

    def set_ports(self, ports):
        if 'ports' not in self.data.keys():
            self.data['ports'] = []
        self.data['ports'].extend(ports)

