from symphony.utils.common import merge_dict
from benedict import BeneDict


class KubeConfigYML(object):
    def __init__(self):
        self.data = {}

    def set_attr(self, new_config):
        """
            New config is a dictionary with the fields to be updated
        """
        merge_dict(self.data, new_config)

    def yml(self):
        return BeneDict(self.data).builtin_dump_yaml_str()


class KubeService(KubeConfigYML):
    def __init__(self, name):
        self.name = name
        self.data = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata':{
                'name': name,
                'labels': {},
            },
            'spec': {
                'ports': [{}],
                'selector': {},
            },
        }


class KubeIntraClusterService(KubeService):
    def __init__(self, name, port):
        self.name = name
        self.port = port
        self.data = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata':{
                'name': name,
                'labels': {}
            },
            'spec': {
                'type': 'ClusterIP',
                'ports': [{'port': port}],
                'selector': {'service-' + name: 'bind'},
            },
        }


class KubeCloudExternelService(KubeService):
    def __init__(self, name, port):
        self.name = name
        self.port = port
        self.data = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata':{
                'name': name,
                'labels': {}
            },
            'spec': {
                'type': 'LoadBalancer',
                'ports': [{'port': port}],
                'selector': {'service-' + name: 'expose'},
            },
        }


class KubeVolume(object):
    def __init__(self, name):
        self.name = name

    def pod_spec(self):
        """
            Returns a spec to fall under Pod: spec:
        """
        raise NotImplementedError
        # return {'name': self.name}


class KubeNFSVolume(KubeVolume):
    def __init__(self, name, server, path):
        self.name = name
        self.server = server
        self.path = path

    def pod_spec(self):
        """
            Returns a spec to fall under Pod: spec:
        """
        return {'name': self.name, 'nfs': {
                'server': self.server,
                'path': self.path
            }
        }


class KubeGitVolume(KubeVolume):
    def __init__(self, name, repository, revision):
        self.name = name
        self.repository = repository
        self.revision = revision

    def pod_spec(self):
        """
            Returns a spec to fall under Pod: spec:
        """
        return {'name': self.name, 'gitRepo': {
                'repository': self.repository,
                'revision': self.revision
            }
        }

# TODO: set command / set args
class KubeContainerYML(KubeConfigYML):
    def __init__(self, name, image):
        self.data = {
                        'name': name,
                        'image': image,
                        'env': [{'name': 'SYMPHONY_ROLE', 'value': name}]
                    }
        self.mounted_volumes = []
        self.pod_yml = None

    def set_command(self, command):
        self.data['command'] = command

    def set_args(self, args):
        self.data['args'] = args

    def set_env(self, name, value):
        for entry in self.data['env']:
            if entry['name'] == name:
                entry['value'] = value
                return
        self.data['env'].append({'name': name, 'value': value})

    def set_envs(self, di):
        for k,v in di.items():
            self.set_env(k, v)

    def mount_volume(self, volume, mount_path):
        assert isinstance(volume, KubeVolume)
        volume_mounts = self.data.get('volumeMounts', [])
        volume_mounts.append({'name':volume.name, 'mountPath': mount_path})
        self.data['volumeMounts'] = volume_mounts
        self.mounted_volumes.append(volume)
        if self.pod_yml is not None:
            self.pod_yml.add_volume(volume)

    def mount_nfs(self, server, path, mount_path, name=None):
        if name is None:
            name = server
        v = KubeNFSVolume(name=name, server=server, path=path)
        self.mount_volume(v, mount_path)

    def mount_git_repo(self, repository, revision, mount_path, name=None):
        if name is None:
            name = strip_repository_name(repository)
        v = KubeGitVolume(name=name,repository=repository,revision=revision)
        self.mount_volume(v, mount_path)

    def resource_request(self, cpu=None, memory=None):
        if cpu is not None:
            merge_dict(self.data, {'resources': {'requests': {'cpu': cpu}}})
        if memory is not None:
            merge_dict(self.data, {'resources': {'requests': {'memory': memory}}})

    def resource_limit(self, cpu=None, memory=None, gpu=None):
        if cpu is not None:
            merge_dict(self.data, {'resources': {'limits': {'cpu': cpu}}})
        if memory is not None:
            merge_dict(self.data, {'resources': {'limits': {'memory': memory}}})
        if gpu is not None: 
            merge_dict(self.data, {'resources': {'limits': {'nvidia.com/gpu': gpu}}})

    def image_pull_policy(self, policy):
        assert policy in ['Always', 'Never', 'IfNotPresent']
        self.data['imagePullPolicy'] = policy


class KubePodYML(KubeConfigYML):
    def __init__(self, name):
        self.data = {
            'apiVersion': 'v1',
            'kind': 'Pod',
            'metadata': {
                'name': name,
                'labels': {
                    'symphony_pg': name
                }
            },
            'spec': {
                'containers': []
            }
        }
        self.container_ymls = []
        self.container_names = set()

    def from_process(process):
        pod_yml = KubePodYML(name=process.name)
        container_yml = KubeContainerYML(process)
        pod_yml.add_container(container_yml)
        return pod_yml

    def add_label(self, key, val):
        self.data['metadata']['labels'][key] = val

    def add_labels(self, **kwargs):
        for k in kwargs:
            self.data['metadata']['labels'][k] = v

    def restart_policy(self, policy):
        assert policy in ['Always', 'OnFailure', 'Never']
        self.data['spec']['restartPolicy'] = policy

    def mount_volume(self, volume, path):
        """
            Mount volume at path for every container in the pod
        """
        self.add_volume(volume)
        for container_yml in self.container_ymls:
            container_yml.mount_volume(volume, path)

    def add_volume(self, *volumes):
        """
            Adds a volume to the list of declared volume of a pod, ignores duplicate name
        """
        declared_volumes = self.data['spec'].get('volumes', [])
        for volume in volumes:
            duplicate = False
            for existing_volume in declared_volumes:
                if volume.name == existing_volume['name']:
                    duplicate = True
                    break
            if duplicate:
                continue
            declared_volumes.append(volume.pod_spec())
        self.data['spec']['volumes'] = declared_volumes

    def add_toleration(self, **kwargs):
        """
            Add taint toleration to a pod
        """
        tolerations = self.data['spec'].get('tolerations', [])
        tolerations.append(kwargs)
        self.data['spec']['tolerations'] = tolerations

    def node_selector(self, key, value):
        """
            Updates node_selector field by the provided selectors
        """
        node_selector = self.data['spec'].get('nodeSelector', {})
        node_selector[key] = value
        self.data['spec']['nodeSelector'] = node_selector

    # Compiling
    def add_container(self, *container_ymls):
        """
            Called by kubecluster at compile time:
            Add the configs from all the continaers
        """
        for container_yml in container_ymls:
            if container_yml.data['name'] in self.container_names:
                continue
            if container_yml.pod_yml is not None and container_yml.pod_yml is not self:
                raise CompilationError('[Error] Adding a container to different pods')
            for volume in container_yml.mounted_volumes:
                self.add_volume(volume)
            self.data['spec']['containers'].append(container_yml.data)
            container_yml.pod_yml = self
            self.container_ymls.append(container_yml)
            self.container_names.add(container_yml.data['name'])

    # def resource_request(self, cpu=None, memory=None):
    #     assert(len(self.container_ymls) == 1)
    #     container_yml = self.container_ymls[0]
    #     container_yml.resource_request(cpu=cpu, memory=memory)
        
    # def resource_limit(self, cpu=None, memory=None, gpu=None):
    #     assert(len(self.container_ymls) == 1)
    #     container_yml = self.container_ymls[0]
    #     container_yml.resource_limit(cpu=cpu, memory=memory, gpu=gpu)

    # def set_command(self, command):
    #     assert(len(self.container_ymls) == 1)
    #     self.data['command'] = command

    # def set_args(self, args):
    #     assert(len(self.container_ymls) == 1)
    #     self.data['args'] = args

    # def image_pull_policy(self, policy):
    #     for container_yml in self.container_ymls:
    #         container_yml.image_pull_policy(policy)

    # def mount_nfs(self, server, path, mount_path, name=None):
    #     if name is None:
    #         name = server
    #     v = KubeNFSVolume(name=name, server=server, path=path)
    #     self.mount_volume(v, mount_path)
    #     return v

    # def mount_git_repo(self, repository, revision, mount_path, name=None):
    #     if name is None:
    #         name = strip_repository_name(repository)
    #     v = KubeGitVolume(name=name,repository=repository,revision=revision)
    #     self.mount_volume(v, mount_path)
    #     return v

    # def set_env(self, name, value):
    #     for container_yml in self.container_ymls:
    #         container_yml.set_env(name, value)
