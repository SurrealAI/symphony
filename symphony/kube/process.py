from symphony.spec import ProcessSpec
from .common import KubeContainerYML, KubePodYML


class KubeProcessSpec(ProcessSpec):
    def __init__(self, name, *, container_image, standalone=True, 
                command=None, args=None, **kwargs):
        super().__init__(name)
        self.container_image = container_image
        self.standalone = standalone
        self.container_yml = KubeContainerYML(self.name, self.container_image)
        if self.standalone:
            self.pod_yml = KubePodYML(self.name)
            self.pod_yml.add_container(self.container_yml)
        if command is not None:
            self.set_command(command)
        if args is not None:
            self.set_args(args)

    def _set_process_group(self, process_group):
        if self.standalone:
            raise ValueError('Stand-alone process {} cannot be added to a process group {}'.format(self.name, process_group.name))
        super()._set_process_group(process_group)
        process_group.pod_yml.add_container(self.container_yml)

    @classmethod
    def load_dict(cls):
        pass

    def dump_dict(self):
        pass

    def set_command(self, command):
        self.container_yml.set_command(command)

    def set_args(self, args):
        self.container_yml.set_args(args)

    def set_env(self, name, value):
        self.container_yml.set_env(name, value)

    def mount_volume(self, volume, mount_path):
        self.container_yml.mount_volume(volume, mount_path)

    def mount_nfs(self, server, path, mount_path, name=None):
        self.container_yml.mount_nfs(server, path, mount_path, name)

    def mount_git_repo(self, repository, revision, mount_path, name=None):
        self.container_yml.mount_git_repo(repository, revision, mount_path, name)

    def resource_request(self, cpu=None, memory=None):
        self.container_yml.resource_request(cpu, memory)

    def resource_limit(self, cpu=None, memory=None, gpu=None):
        self.container_yml.resource_limit(cpu, memory, gpu)

    def image_pull_policy(self, policy):
        self.container_yml.image_pull_policy(policy)

    # Pod level
    def restart_policy(self, policy):
        assert self.standalone, 'Restart policy should be configured at process group level'
        self.pod_yml.restart_policy(policy)

    def add_labels(self, **kwargs):
        assert self.standalone, 'Labels for process {} should be configured at process group level'.format(self.name)
        self.pod_yml.add_labels(**kwargs)

    def add_label(self, key, val):
        assert self.standalone, 'Labels for process {} should be configured at process group level'.format(self.name)
        self.pod_yml.add_label(key, val)

    def add_toleration(self, **kwargs):
        assert self.standalone, 'Tolerations for process {} should be configured at process group level'.format(self.name)
        self.pod_yml.add_toleration(**kwargs)

    def node_selector(self, key, value):
        assert self.standalone, 'Node selector for process {} should be configured at process group level'.format(self.name)
        self.pod_yml.node_selector(key, value)
