from symphony.spec import ProcessSpec
from symphony.utils.common import check_valid_hostname
from .builder import DockerServiceYML


class DockerProcessSpec(ProcessSpec):
    def __init__(self, name, container_image):
        check_valid_hostname(name)
        super().__init__(name)
        self.container_image = container_image
        self.service_yml = DockerServiceYML(self.name, self.container_image)

    def _load_dict(self, di):
        super()._load_dict(di)
        self.container_image = di['container_image']
        self.service_yml = DockerServiceYML.load(di['service_yml'])

    def dump_dict(self):
        di = super().dump_dict()
        di['container_image'] = self.container_image
        di['service_yml'] = self.service_yml.save()
        return di

    def yml_dict(self):
        return self.service_yml.data

    def yml(self):
        return self.yml_dict().dump_yaml_str()

    def set_hostname(self, hostname):
        check_valid_hostname(hostname)
        self.service_yml.set_hostname(hostname)

    def set_env(self, name, value):
        self.service_yml.set_env(name, value)

    def set_envs(self, di):
        for name, value in di.items():
            self.service_yml.set_env(name, value)

    def set_port(self, port):
        self.service_yml.set_port(port)

    def set_ports(self, ports):
        self.service_yml.set_ports(ports)

    # def set_envs(self, di):
    #     self.container_yml.set_envs(di)

    # def mount_volume(self, volume, mount_path):
    #     self.container_yml.mount_volume(volume, mount_path)

    # def mount_nfs(self, server, path, mount_path, name=None):
    #     self.container_yml.mount_nfs(server, path, mount_path, name)
    #
    # def mount_git_repo(self, repository, revision, mount_path, name=None):
    #     self.container_yml.mount_git_repo(repository, revision, mount_path, name)
    #
    # def mount_host_path(self, path, mount_path, hostpath_type='', name=None):
    #     self.container_yml.mount_host_path(path, mount_path, hostpath_type, name)
    #
    # def mount_empty_dir(self, name, use_memory, mount_path):
    #     self.container_yml.mount_empty_dir(mount_path, use_memory, name)

