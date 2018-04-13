from symphony.cluster.cluster import CompilationError
from symphony.core.address import AddressBookData
import yaml
import collections
import itertools
from io import StringIO

def merge_dict(d, u):
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            d[k] = update(d.get(k, {}), v)
        elif isinstance(v, list):
            d[k] = d.get(k, {}) + v
        else:
            d[k] = v
    return d


def dump_yml(di):
    stream = StringIO()
    yaml.dump(
        di,
        stream,
        default_flow_style=False,
        indent=2
    )
    return stream.getvalue()


class KubeConfigYML(object):
    def __init__(self):
        self.data = {}

    def set_attr(self, new_config):
        """
            New config is a dictionary with the fields to be updated
        """
        update(self.data, new_config)


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
            'type': 'ClusterIP',
            'metadata':{
                'name': name,
                'labels': {}
            },
            'spec': {
                'ports': [{'port': port}],
                'selector': {'binds': name},
            },
        }


class KubeCloudExternelService(KubeService):
    def __init__(self, name, port):
        self.name = name
        self.port = port
        self.data = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'type': 'LoadBalancer',
            'metadata':{
                'name': name,
                'labels': {}
            },
            'spec': {
                'ports': [{'port': port}],
                'selector': {'exposes': name},
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


class KubeContainerYML(KubeConfigYML):
    def __init__(self, process):
        if process.container_image is None:
            raise CompilationError("[Error] Process {} has no container_image specified. It is incompatible with Kubernetes ".format(process.name))
        if process.args is None:
            raise CompilationError("Process {} has no args specified. It is incompatible with Kubernetes".format(process.name))
        self.data = {
                        'name': process.name,
                        'image': process.container_image,
                        'args': process.args,
                        'env': [{'name': 'SYMPHONY_ROLE', 'value': process.name}]
                    }
        self.mounted_volumes = []
        self.pod_yml = None

    def set_env(self, name, value):
        self.data['env'].append({'name': name, 'value': value})

    def mount_volume(self, volume, path):
        assert isinstance(volume, KubeVolume)
        volume_mounts = self.data.get('volumeMounts', [])
        volumeMounts.append({'name':volume.name, 'path': path})
        self.data['volumeMounts'] = volume_mounts
        self.mounted_volumes.append(volume)
        if self.pod_yml is not None:
            self.pod_yml.add_volume(volume)

    def resource_request(self, cpu=None, memory=None):
        if cpu is not None:
            self.data = merge_dict(self.data, {'resources': {'requests': {'cpu': cpu}}})
        if memory is not None:
            self.data = merge_dict(self.data, {'resources': {'requests': {'memory': memory}}})

    def resource_limit(self, cpu=None, memory=None, gpu=None):
        if cpu is not None:
            self.data = merge_dict(self.data, {'resources': {'limits': {'cpu': cpu}}})
        if memory is not None:
            self.data = merge_dict(self.data, {'resources': {'limits': {'memory': memory}}})
        if gpu is not None: 
            self.data = merge_dict(self.data, {'resources': {'limits': {'nvidia.com/gpu': gpu}}})


class KubePodYML(KubeConfigYML):
    def __init__(self, process_group=None, name=None):
        if process_group is not None:
            name = process_group.name
        else:
            if name is None:
                raise ValueError('Cannot initialize KubePodConfig without a process_group or a name')
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

    def restart_policy(self, policy):
        assert policy in ['Always', 'OnFailure', 'Never']
        self.data['spec']['restartPolicy'] = policy

    def add_volume(self, *volumes):
        """
            Adds a volume to the list of declared volume of a pod, ignores duplicate name
        """
        declared_volumes = self.data.get('volumes', [])
        for volume in volumes:
            duplicate = False
            for existing_volume in declared_volumes:
                if volume.name == existing_volume['name']:
                    duplicate = True
                    break
            if duplicate:
                continue
        declared_volumes.append(volume.pod_spec())

    def add_toleration(self, key, operator, effect, **kwargs):
        """
            Add taint toleration to a pod
        """
        tolerations = self.data['spec'].get('tolerations', [])
        assert effect in ['NoExecute', 'NoSchedule', 'PreferNoSchedule']
        kwargs['key'] = key
        kwargs['operator'] = operator
        kwargs['effect'] = effect
        tolerations.append(kwargs)

    def update_node_selectors(self, **kwargs):
        """
            Updates node_selector field by the provided selectors
        """
        existing = self.data['spec'].get('nodeSelector', {})
        merge_dict(existing, kwargs)

    # Compiling
    def add_container(self, *container_ymls):
        """
            Called by kubecluster at compile time:
            Add the configs from all the continaers
        """
        # TODO: fix
        for container_yml in container_ymls:
            if container_yml.data['name'] in self.container_names:
                continue
            if container_yml.pod_yml is not None:
                raise CompilationError('[Error] Adding a container to a pod twice')
            for volume in container_yml.mounted_volumes:
                self.add_volume(volume)
            self.data['spec']['containers'].append(container_yml.data)
            container_yml.pod_yml = self
            self.container_ymls.append(container_yml)
            self.container_names.add(container_yml.data['name'])


class KubeExperiment(object):
    #TODO: Minikube
    def __init__(self, experiment, portrange=None):
        self.pods = {}
        self.provided_services = {}
        self.exposed_services = {}
        self.reserved_ports = {}
        self.experiment = experiment
        self.portrange = portrange
        if self.portrange is None:
            self.portrange = list(reversed(range(7000, 8000)))

    def compile(self):
        for process_group in self.experiment.process_groups.values():
            self.initialize_process_group(process_group)
        for process in self.experiment.processes.values():
            if process.process_group is None:
                self.initialize_process(process)

        self.declare_services()
        self.assign_addresses()
        # TODO: static port services
        
        components = itertools.chain(self.provided_services.values(),
                        self.exposed_services.values(),
                        self.pods.values())
        return ''.join(['---\n' + dump_yml(x.data) for x in components])
        
    def assign_addresses(self):
        # print(self.provided_services)
        # print(self.exposed_services)
        # print(self.reserved_ports)
        for process in self.experiment.processes.values():
            ab_data = AddressBookData()
            for exposed_service_name in process.exposed_services:
                exposed_service = self.exposed_services[exposed_service_name]
                ab_data.add_provider(exposed_service.name, exposed_service_name, exposed_service.port)
        
            for provided_service_name in process.provided_services:
                provided_service = self.provided_services[provided_service_name]
                ab_data.add_provider(provided_service.name, 
                                provided_service.name, provided_service.port)

            for requested_service_name in process.requested_services:
                if not requested_service_name in self.provided_services:
                    raise CompilationError('[Error] Process {} requests non-declared service {}'.format(process.name, requested_service_name))
                requested_service = self.provided_services[requested_service_name]
                ab_data.add_requester(requested_service.name, 
                                requested_service.name, requested_service.port)

            for reserved_port_name in process.reserved_ports:
                reserved_port = self.reserved_ports[reserved_port_name]
                ab_data.add_requester(reserved_port_name, '127.0.0.1', reserved_port)
                ab_data.add_provider(reserved_port_name, '127.0.0.1', reserved_port)

            json_string = ab_data.dumps()
            if process.process_group is None:
                pod_yml = process.cluster_configs['kubernetes']
                pod_yml.container_ymls[0].set_env('SYMPHONY_AB_DATA', json_string)
            else:
                container_yml = process.cluster_configs['kubernetes']
                container_yml.set_env('SYMPHONY_AB_DATA', json_string)

    def declare_services(self):
        """
            Loop through all processes and assign addresses for all declared services
        """
        for process in self.experiment.processes.values():
            for reserved_port_name in process.reserved_ports:
                if reserved_port_name in self.reserved_ports:
                    continue
                port = process.reserved_ports[reserved_port_name]
                if port is None:
                    port = self.get_port()
                if port in self.portrange:
                    self.portrange.remove(port)
                self.reserved_ports[reserved_port_name] = port
        for process in self.experiment.processes.values(): 
            for exposed_service_name in process.exposed_services:
                if exposed_service_name in self.exposed_services:
                    continue
                port = process.exposed_services[exposed_service_name]
                if port is None:
                    port = self.get_port()
                print(exposed_service_name)
                service = KubeCloudExternelService(exposed_service_name, port)
                self.exposed_services[service.name] = service
            for provided_service_name in process.provided_services:
                if provided_service_name in self.provided_services:
                    continue
                port = process.provided_services[provided_service_name]
                if port is None:
                    port = self.get_port()
                service = KubeIntraClusterService(provided_service_name, port)
                self.provided_services[service.name] = service
            

    def get_port(self):
        if len(self.portrange) == 0:
            raise CompilationError('[Error] Experiment {} ran out of ports on Kubernetes.'.format(self.experiment.name))
        return self.portrange.pop()

    def initialize_process_group(self, process_group):
        """
            Generate default configs if any is missing
        """
        pod_yml = process_group.cluster_configs.get('kubernetes', None)
        if pod_yml is None:
            print("[Info] Generating default pod config for process group {}".format(process_group.name))
            pod_yml = KubePodYML(process_group)
            process_group.cluster_configs['kubernetes'] = pod_yml
        assert isinstance(pod_yml, KubePodYML)
        self.pods[process_group.name] = pod_yml

        for process in process_group.processes.values():
            container_yml = process.cluster_configs.get('kubernetes', None)
            if container_yml is None:
                print("[Info] Generating default container config for process {}".format(process.name))
                container_yml = KubeContainerYML(process)
                process.cluster_configs['kubernetes'] = container_yml
            assert isinstance(container_yml, KubeContainerYML)
            pod_yml.add_container(container_yml)

    def initialize_process(self, process):
        """
            Generate default configs if any is missing. For processes without a process group
        """
        pod_yml = process.cluster_configs.get('kubernetes', None)
        if pod_yml is None:
            print("[Info] Generating default pod config for process {}".format(process.name))
            pod_yml = KubePodYML.from_process(process)
            process.cluster_configs['kubernetes'] = pod_yml
        # print(process.name)
        # print(process.process_group)
        # print(pod_yml)
        assert isinstance(pod_yml, KubePodYML)
        self.pods[process.name] = pod_yml


class KubeCluster(object):
    def __init__(self):
        pass

    def launch(self, experiment): # TODO: partial launch
        kube_exp = experiment.cluster_configs.get('kubernetes', None)
        if kube_exp is None:
            kube_exp = KubeExperiment(experiment)
            experiment.cluster_configs['kubernetes'] = kube_exp
        launch_plan = kube_exp.compile()
        print(launch_plan)

