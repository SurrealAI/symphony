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







        


# class Service(KubeConfigYML):
#     def __init__(self, name):
#         super().__init__()
#         self.name = name
#         self.data = BeneDict({
#             'apiVersion': 'v1',
#             'kind': 'Service',
#             'metadata':{
#                 'name': name,
#                 'labels': {},
#             },
#             'spec': {
#                 'ports': [{}],
#                 'selector': {},
#             },
#         })


# class _KubeVolumeRegistry(type):
#     registry = {}
#
#     def __new__(cls, name, bases, class_dict):
#         cls = type.__new__(cls, name, bases, class_dict)
#         _KubeVolumeRegistry.registry[cls.__name__] = cls
#         return cls


# class KubeVolume(metaclass=_KubeVolumeRegistry):
#     """
#     Simple wrapper for some volumes that we are using
#     https://kubernetes.io/docs/concepts/storage/volumes/#types-of-volumes
#     """
#     def __init__(self, name):
#         self.name = name
#
#     def pod_spec(self):
#         """
#             Returns a spec to fall under Pod: spec:
#         """
#         raise NotImplementedError
#         # return {'name': self.name}
#
#     @classmethod
#     def load(cls, config):
#         """
#         config is a dict of "type": "KubeVolumeClass" and init kwargs
#         """
#         assert 'type' in config
#         config = config.copy()
#         volume_cls_name = config.pop('type')
#         assert volume_cls_name in _KubeVolumeRegistry.registry, \
#             'volume type not found in KubeVolumeRegistry'
#         volume_cls = _KubeVolumeRegistry.registry[volume_cls_name]
#         return volume_cls(**config)
#
#     def save(self):
#         raise NotImplementedError


# class KubeHostPathVolume(KubeVolume):
#     def __init__(self, name, path, hostpath_type=''):
#         """
#             path: directory location on host
#             hostpath_type: optional, type of hostpath
#         """
#         super().__init__(name)
#         self.hostpath_type = hostpath_type
#         self.path = path
#
#     def pod_spec(self):
#         """
#             Returns a spec to fall under Pod: spec:
#         """
#         return BeneDict({
#             'name': self.name,
#             'hostPath': {
#                 'hostpath_type': self.hostpath_type,
#                 'path': self.path,
#                 },
#             })
#
#     def save(self):
#         return {
#             'name': self.name,
#             'hostpath_type': self.hostpath_type,
#             'path': self.path,
#             'type': self.__class__.__name__
#         }


# class KubeContainerYML(KubeConfigYML):
#     def __init__(self, name, image):
#         super().__init__()
#         self.data = BeneDict({
#             'name': name,
#             'image': image,
#             'env': [{'name': 'SYMPHONY_ROLE', 'value': name}]
#         })
#         self.mounted_volumes = []
#         self.pod_yml = None
#
#     @classmethod
#     def load(cls, di):
#         instance = cls('', '')
#         instance.data = BeneDict(di['data'])
#         instance.mounted_volumes = [KubeVolume.load(x) for x in di['mounted_volumes']]
#         return instance
#
#     def save(self):
#         di = {}
#         di['data'] = self.data
#         di['mounted_volumes'] = [x.save() for x in self.mounted_volumes]
#         return di
#
#     def set_command(self, command):
#         self.data.command = command
#
#     def set_args(self, args):
#         self.data.args = args
#
#     def set_env(self, name, value):
#         name = str(name)
#         value = str(value)
#         for entry in self.data['env']:
#             if entry.name == name:
#                 entry.value = value
#                 return
#         self.data.env.append(BeneDict({'name': name, 'value': value}))
#
#     def set_envs(self, di):
#         for k, v in di.items():
#             self.set_env(k, v)
#
#     def mount_volume(self, volume, mount_path):
#         assert isinstance(volume, KubeVolume)
#         volume_mounts = self.data.get('volumeMounts', [])
#         volume_mounts.append(BeneDict({'name':volume.name, 'mountPath': mount_path}))
#         self.data['volumeMounts'] = volume_mounts
#         self.mounted_volumes.append(volume)
#         if self.pod_yml is not None:
#             self.pod_yml.add_volume(volume)
#
#     def mount_nfs(self, server, path, mount_path, name=None):
#         if name is None:
#             name = server
#         v = KubeNFSVolume(name=name, server=server, path=path)
#         self.mount_volume(v, mount_path)
#
#     def mount_host_path(self, path, mount_path, hostpath_type='', name=None):
#         if name is None:
#             name = path.split('/')[-1]
#         v = KubeHostPathVolume(name=name, path=path, hostpath_type=hostpath_type)
#         self.mount_volume(v, mount_path)
#
#     def mount_empty_dir(self, name, use_memory, mount_path):
#         v = KubeEmptyDirVolume(name=name, use_memory=use_memory)
#         self.mount_volume(v, mount_path)


# class KubePodYML(KubeConfigYML):
#     def __init__(self, name):
#         super().__init__()
#         self.data = BeneDict({
#             'apiVersion': 'v1',
#             'kind': 'Pod',
#             'metadata': {
#                 'name': name,
#                 'labels': {
#                     'symphony_pg': name
#                 }
#             },
#             'spec': {
#                 'containers': []
#             }
#         })
#         self.container_ymls = []
#         self.container_names = set()
#
#     @classmethod
#     def load(cls, di):
#         instance = cls('')
#         instance.data = di['data']
#         return instance
#
#     def save(self):
#         data = copy.deepcopy(self.data)
#         data.spec.containers = []
#         return {'data': data}
#
#     def add_label(self, key, val):
#         self.data.metadata.labels[key] = val
#
#     def add_labels(self, **kwargs):
#         for k, v in kwargs.items():
#             self.data['metadata']['labels'][k] = v
#
#     def restart_policy(self, policy):
#         assert policy in ['Always', 'OnFailure', 'Never']
#         self.data['spec']['restartPolicy'] = policy
#
#     def mount_volume(self, volume, path):
#         """
#             Mount volume at path for every container in the pod
#         """
#         self.add_volume(volume)
#         for container_yml in self.container_ymls:
#             container_yml.mount_volume(volume, path)
#
#     def add_volume(self, *volumes):
#         """
#             Adds a volume to the list of declared volume of a pod, ignores duplicate name
#         """
#         declared_volumes = self.data['spec'].get('volumes', [])
#         for volume in volumes:
#             duplicate = False
#             for existing_volume in declared_volumes:
#                 if volume.name == existing_volume['name']:
#                     duplicate = True
#                     break
#             if duplicate:
#                 continue
#             declared_volumes.append(volume.pod_spec())
#         self.data['spec']['volumes'] = declared_volumes
#
#     def add_toleration(self, **kwargs):
#         """
#             Add taint toleration to a pod
#         """
#         tolerations = self.data['spec'].get('tolerations', [])
#         tolerations.append(kwargs)
#         self.data['spec']['tolerations'] = tolerations
#
#     def node_selector(self, key, value):
#         """
#             Updates node_selector field by the provided selectors
#         """
#         node_selector = self.data['spec'].get('nodeSelector', {})
#         node_selector[key] = value
#         self.data['spec']['nodeSelector'] = node_selector
#
#     # Compiling
#     def add_container(self, *container_ymls):
#         """
#             Called by kubecluster at compile time:
#             Add the configs from all the continaers
#         """
#         for container_yml in container_ymls:
#             if container_yml.data['name'] in self.container_names:
#                 continue
#             if container_yml.pod_yml is not None and container_yml.pod_yml is not self:
#                 raise ValueError('[Error] Adding a container to different pods')
#             for volume in container_yml.mounted_volumes:
#                 self.add_volume(volume)
#             self.data['spec']['containers'].append(container_yml.data)
#             container_yml.pod_yml = self
#             self.container_ymls.append(container_yml)
#             self.container_names.add(container_yml.data['name'])
