from symphony.spec import ProcessGroupSpec
from symphony.utils.common import sanitize_name_kubernetes, strip_repository_name
from .process import KubeProcessSpec
from .builder import KubePodYML, KubeNFSVolume, KubeGitVolume


class KubeProcessGroupSpec(ProcessGroupSpec):
    _ProcessClass = KubeProcessSpec

    def __init__(self, name):
        name = sanitize_name_kubernetes(name)
        super().__init__(name)
        self.pod_yml = KubePodYML(self.name)

    def new_process(self, *args, **kwargs):
        if self._ProcessClass is None:
            raise NotImplementedError('Please define class variable _ProcessClass')
        kwargs['standalone'] = False
        p = self._ProcessClass(*args, **kwargs)
        self.add_process(p)
        return p

    def _load_dict(self, di):
        self.pod_yml = KubePodYML.load(di['pod_yml'])
        super()._load_dict(di)

    def dump_dict(self):
        di = super().dump_dict()
        di['pod_yml'] = self.pod_yml.save()
        return di

    def yml(self):
        return self.pod_yml.yml()

    ### Pod level 

    def add_labels(self, **kwargs):
        self.pod_yml.add_labels(**kwargs)

    def add_label(self, key, val):
        self.pod_yml.add_label(key, val)

    def restart_policy(self, policy):
        self.pod_yml.restart_policy(policy)

    def add_toleration(self, **kwargs):
        self.pod_yml.add_toleration(**kwargs)

    def node_selector(self, key, value):
        self.pod_yml.node_selector(key, value)

    ### Batch methods
    def mount_volume(self, volume, path):
        self.pod_yml.mount_volume(volume, path)

    def image_pull_policy(self, policy):
        for process in self.list_processes():
            process.image_pull_policy(policy)

    def mount_nfs(self, server, path, mount_path, name=None):
        if name is None:
            name = server
        v = KubeNFSVolume(name=name, server=server, path=path)
        for process in self.list_processes():
            process.mount_volume(v, mount_path)

    def mount_git_repo(self, repository, revision, mount_path, name=None):
        if name is None:
            name = strip_repository_name(repository)
        v = KubeGitVolume(name=name,repository=repository,revision=revision)
        for process in self.list_processes():
            process.mount_volume(v, mount_path)

    def set_env(self, name, value):
        for process in self.list_processes():
            process.set_env(name, value)

    def set_envs(self, di):
        for process in self.list_processes():
            process.set_envs(di)
