from symphony.spec import ProcessSpec
from symphony.utils.common import sanitize_name_kubernetes, print_err
from .builder import KubeContainerYML, KubePodYML
from benedict.data_format import load_yaml_str


class KubeProcessSpec(ProcessSpec):
    def __init__(self, name, *, container_image=None, standalone=True, 
                command=None, args=None, **kwargs):
        name = sanitize_name_kubernetes(name)
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
    
    def _load_dict(self, di):
        super()._load_dict(di)
        self.container_image = di['container_image']
        self.standalone = di['standalone']

        self.container_yml = KubeContainerYML.load(di['container_yml'])

        if self.standalone:
            self.pod_yml = KubePodYML.load(di['pod_yml'])
            self.pod_yml.add_container(self.container_yml)

    def dump_dict(self):
        di = super().dump_dict()
        di['container_image'] = self.container_image
        di['standalone'] = self.standalone
        di['container_yml'] = self.container_yml.save()
        if self.standalone:
            di['pod_yml'] = self.pod_yml.save()
        return di

    def yml(self):
        assert self.standalone, 'Yml for process {} should be configured at process group level'.format(self.name)
        return self.pod_yml.yml()

    ### Container level 

    def set_command(self, command):
        if not isinstance(command, list):
            print_err('[Warning] command {} for KubernetesProcess {} must be a list'.format(command, self.name))
            command = [command]
        self.container_yml.set_command(command)

    def set_args(self, args):
        if not isinstance(args, list):
            print_err('[Warning] args {} for KubernetesProcess {} must be a list'.format(args, self.name))
            args = [args]
        self.container_yml.set_args(args)

    def set_env(self, name, value):
        self.container_yml.set_env(name, value)

    def set_envs(self, di):
        self.container_yml.set_envs(di)

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

    ### Pod level
    def restart_policy(self, policy):
        assert self.standalone, 'Restart policy for process {} should be configured at process group level'.format(self.name)
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
