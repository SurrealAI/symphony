from symphony.cluster.cluster import CompilationError, Cluster
from symphony.core.address import AddressBookData
from symphony.core.fs_manager import FSManager
import yaml
import collections
import itertools
from io import StringIO
# TODO: fix this
from surreal.utils.ezdict import EzDict

def merge_dict(d, u):
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            d[k] = merge_dict(d.get(k, {}), v)
        elif isinstance(v, list):
            d[k] = d.get(k, []) + v
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
                'selector': {'service-' + name: 'provide'},
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
        volume_mounts.append({'name':volume.name, 'path': path})
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

    def image_pull_policy(self, policy):
        assert policy in ['Always', 'Never', 'IfNotPresent']
        self.data['imagePullPolicy'] = policy

    # def node_selector(self, key, value):
    #     """
    #         Set node selector of pod to be 'key: value'
    #     """
    #     self.pod_yml.node_selector(key, value)


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

    def add_labels(self, **kwargs):
        for k in kwargs:
            self.data['metadata']['labels'][k] = v

    def add_label(self, key, val):
        self.data['metadata']['labels'][key] = val

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
        self.data['spec']['node_selector'] = node_selector

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

    def resource_request(self, cpu=None, memory=None):
        assert(len(self.container_ymls) == 1)
        container_yml = self.container_ymls[0]
        container_yml.resource_request(cpu=cpu, memory=memory)
        
    def resource_limit(self, cpu=None, memory=None, gpu=None):
        assert(len(self.container_ymls) == 1)
        container_yml = self.container_ymls[0]
        container_yml.resource_limit(cpu=cpu, memory=memory, gpu=gpu)

    def image_pull_policy(self, policy):
        for container_yml in self.container_ymls:
            container_yml.image_pull_policy(policy)


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
        self.initialize_configs()

        self.declare_services()
        self.assign_addresses()
        # TODO: static port services
        
        components = itertools.chain(self.provided_services.values(),
                        self.exposed_services.values(),
                        self.pods.values())
        return ''.join(['---\n' + dump_yml(x.data) for x in components])

    def initialize_configs(self):
        """
            Intialize kubernetes configs for all parts of the experiment.
        """
        for process_group in self.experiment.process_groups.values():
            self.initialize_process_group(process_group)
        for process in self.experiment.processes.values():
            if process.process_group is None:
                self.initialize_process(process)
        
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
            if process.process_group is None:
                pod_yml = process.cluster_configs['kubernetes']
            else:
                pod_yml = process.process_group.cluster_configs['kubernetes']
            for exposed_service_name in process.exposed_services:
                if exposed_service_name in self.exposed_services:
                    continue
                port = process.exposed_services[exposed_service_name]
                if port is None:
                    port = self.get_port()
                service = KubeCloudExternelService(exposed_service_name, port)
                pod_yml.add_label('service-' + exposed_service_name, 'expose')
                self.exposed_services[service.name] = service
            for provided_service_name in process.provided_services:
                if provided_service_name in self.provided_services:
                    continue
                port = process.provided_services[provided_service_name]
                if port is None:
                    port = self.get_port()
                service = KubeIntraClusterService(provided_service_name, port)
                pod_yml.add_label('service-' + provided_service_name, 'provide')
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


class KubeCluster(Cluster):
    # TODO: make launch work
    # TODO: username scoping
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.fs = FSManager()

    def launch(self, experiment): # TODO: partial launch
        kube_exp = experiment.cluster_configs.get('kubernetes', None)
        if kube_exp is None:
            kube_exp = KubeExperiment(experiment)
            experiment.cluster_configs['kubernetes'] = kube_exp
        launch_plan = kube_exp.compile()

        if self.dry_run:
            print(launch_plan)
        else:
            self.fs.save_experiment(experiment)
            launch_plan_file = self.fs.save_launch_plan(self, experiment.name, launch_plan, 'kubernetes')
            #TODO: persist yaml file
            self.run('create namespace ' + experiment.name)
            self.run('create -f "{}" --namespace {}'.format(launch_plan_file, experiment.name))

    def run(self, cmd, program='kubectl'):
        super().run(cmd, program)

    def run_raw(self, cmd, program='kubectl', print_cmd=False):
        super().run_raw(cmd, program, print_cmd)

    def run_verbose(self, cmd, print_out=True, raise_on_error=False, program='kubectl'):
        super().run_verbose(cmd, print_out=print_out,raise_on_error=raise_on_error,program=program)

    def current_context(self):
        out, err, retcode = self.run_verbose(
            'config current-context', print_out=False, raise_on_error=True
        )
        return out

    def current_namespace(self):
        """
        Parse from `kubectl config view`
        """
        config = self.config_view()
        current_context = self.current_context()
        if self.dry_run:
            return 'dummy-namespace'
        for context in config['contexts']:
            if context['name'] == current_context:
                return context['context']['namespace']
        raise RuntimeError('INTERNAL: current context not found')

    def list_namespaces(self):
        all_names = self.query_resources('namespace', output_format='name')
        # names look like namespace/<actual_name>, need to postprocess
        return [n.split('/')[-1] for n in all_names]

    def set_namespace(self, namespace):
        """
        https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/
        After this call, all subsequent `kubectl` will default to the namespace
        """
        check_valid_dns(namespace)
        _, _, retcode = self.run_verbose(
            'config set-context $(kubectl config current-context) --namespace='
            + namespace,
            print_out=True, raise_on_error=False
        )
        if not self.dry_run and retcode == 0:
            print('successfully switched to namespace `{}`'.format(namespace))

    def _deduplicate_with_order(self, seq):
        """
        https://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-in-whilst-preserving-order
        deduplicate list while preserving order
        """
        return list(OrderedDict.fromkeys(seq))

    def fuzzy_match_namespace(self, name, max_matches=10):
        """
        Fuzzy match namespace, precedence from high to low:
        1. exact match of <prefix + name>, if prefix option is turned on in ~/.surreal.yml
        2. exact match of <name> itself
        3. starts with <prefix + name>, sorted alphabetically
        4. starts with <name>, sorted alphabetically
        5. contains <name>, sorted alphabetically
        Up to `max_matches` number of matches

        Returns:
            - string if the matching is exact
            - OR list of fuzzy matches
        """
        all_names = self.list_namespaces()
        prefixed_name = self.prefix_username(name)
        if prefixed_name in all_names:
            return prefixed_name
        if name in all_names:
            return name
        # fuzzy matching
        matches = []
        matches += sorted([n for n in all_names if n.startswith(prefixed_name)])
        matches += sorted([n for n in all_names if n.startswith(name)])
        matches += sorted([n for n in all_names if name in n])
        matches = self._deduplicate_with_order(matches)
        return matches[:max_matches]

    def query_resources(self, resource,
                        output_format,
                        names=None,
                        labels='',
                        fields='',
                        namespace=''):
        """
        Query all items in the resource with `output_format`
        JSONpath: https://kubernetes.io/docs/reference/kubectl/jsonpath/
        label selectors: https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/

        Args:
            resource: pod, service, deployment, etc.
            output_format: https://kubernetes.io/docs/reference/kubectl/overview/#output-options
              - custom-columns=<spec>
              - custom-columns-file=<filename>
              - json: returns a dict
              - jsonpath=<template>
              - jsonpath-file=<filename>
              - name: list
              - wide
              - yaml: returns a dict
            names: list of names to get resource, mutually exclusive with
                label and field selectors. Should only specify one.
            labels: label selector syntax, comma separated as logical AND. E.g:
              - equality: mylabel=production
              - inequality: mylabel!=production
              - set: mylabel in (group1, group2)
              - set exclude: mylabel notin (group1, group2)
              - don't check value, only check key existence: mylabel
              - don't check value, only check key nonexistence: !mylabel
            fields: field selector, similar to label selector but operates on the
              pod fields, such as `status.phase=Running`
              fields can be found from `kubectl get pod <mypod> -o yaml`

        Returns:
            dict if output format is yaml or json
            list if output format is name
            string from stdout otherwise
        """
        if names and (labels or fields):
            raise ValueError('names and (labels or fields) are mutually exclusive')
        cmd = 'get ' + resource
        cmd += self._get_ns_cmd(namespace)
        if names is None:
            cmd += self._get_selectors(labels, fields)
        else:
            assert isinstance(names, (list, tuple))
            cmd += ' ' + ' '.join(names)
        if '=' in output_format:
            # quoting the part after jsonpath=<...>
            prefix, arg = output_format.split('=', 1)
            output_format = prefix + '=' + shlex.quote(arg)
        cmd += ' -o ' + output_format
        out, _, _ = self.run_verbose(cmd, print_out=False, raise_on_error=True)
        if output_format == 'yaml':
            return EzDict.loads_yaml(out)
        elif output_format == 'json':
            return EzDict.loads_json(out)
        elif output_format == 'name':
            return out.split('\n')
        else:
            return out

    def query_jsonpath(self, resource,
                       jsonpath,
                       names=None,
                       labels='',
                       fields='',
                       namespace=''):
        """
        Query items in the resource with jsonpath
        https://kubernetes.io/docs/reference/kubectl/jsonpath/
        This method is an extension of list_resources()
        Args:
            resource:
            jsonpath: make sure you escape dot if resource key string contains dot.
              key must be enclosed in *single* quote!!
              e.g. {.metadata.labels['kubernetes\.io/hostname']}
              you don't have to do the range over items, we take care of it
            labels: see `list_resources`
            fields:

        Returns:
            a list of returned jsonpath values
        """
        if '{' not in jsonpath:
            jsonpath = '{' + jsonpath + '}'
        jsonpath = '{range .items[*]}' + jsonpath + '{"\\n\\n"}{end}'
        output_format = "jsonpath=" + jsonpath
        out = self.query_resources(
            resource=resource,
            names=names,
            output_format=output_format,
            labels=labels,
            fields=fields,
            namespace=namespace
        )
        return out.split('\n\n')

    def config_view(self):
        """
        kubectl config view
        Generates a yaml of context and cluster info
        """
        out, err, retcode = self.run_verbose(
            'config view', print_out=False, raise_on_error=True
        )
        return EzDict.loads_yaml(out)

    def external_ip(self, pod_name, namespace=''):
        """
        Returns:
            "<ip>:<port>"
        """
        tb = self.query_resources('svc', 'yaml',
                                  names=[pod_name], namespace=namespace)
        conf = tb.status.loadBalancer
        if not ('ingress' in conf and 'ip' in conf.ingress[0]):
            return ''
        ip = conf.ingress[0].ip
        port = tb.spec.ports[0].port
        return '{}:{}'.format(ip, port)

    def _get_ns_cmd(self, namespace):
        if namespace:
            return ' --namespace ' + namespace
        else:
            return ''

    def _get_logs_cmd(self, pod_name, container_name,
                      follow, since=0, tail=-1, namespace=''):
        return 'logs {} {} {} --since={} --tail={}{}'.format(
            pod_name,
            container_name,
            '--follow' if follow else '',
            since,
            tail,
            self._get_ns_cmd(namespace)
        )

    def get_pod_container(self, experiment_name, process_name):
        experiment = self.fs.load_experiment(experiment_name)
        for process in experiment.processes.values():
            if process.name == process_name:
                if process.process_group is not None:
                    pod_name = process.process_group.name
                else:
                    pod_name = process.name
                return pod_name, process_name
        raise ValueError('[Error] Cannot find processs with name: {}'.format(process_name))

    def logs(self,process_name,since=0,tail=100,experiment_name=None):
        """
        kubectl logs <pod_name> <container_name> --follow --since= --tail=
        https://kubernetes-v1-4.github.io/docs/user-guide/kubectl/kubectl_logs/

        Returns:
            stdout string
        """
        if experiment_name is None:
            experiment_name = self.current_namespace()
        pod_name, container_name = get_pod_container(experiment_name, process_name)
        out, err, retcode = self.run_verbose(
            self._get_logs_cmd(
                pod_name, process_name, follow=False,
                since=since, tail=tail, namespace=experiment_name
            ),
            print_out=False,
            raise_on_error=False
        )
        if retcode != 0:
            return ''
        else:
            return out

    def describe(self, process_name, experiment_name=None):
        if experiment_name is None:
            experiment_name = self.current_namespace()
        pod_name, container_name = self.get_pod_container(experiment_name, process_name)
        cmd = 'describe pod ' + pod_name + self._get_ns_cmd(experiment_name)
        return self.run_verbose(cmd, print_out=True, raise_on_error=False)

    def print_logs(self, process_name,follow=False,since=0,tail=100,experiment_name=None):
        """
        kubectl logs <pod_name> <container_name>
        No error checking, no string caching, delegates to os.system
        """
        if experiment_name is None:
            experiment_name = self.current_namespace()
        pod_name, container_name = self.get_pod_container(experiment_name, process_name)
        cmd = self._get_logs_cmd(
            pod_name, container_name, follow=follow,
            since=since, tail=tail, namespace=namespace
        )
        self.run_raw(cmd)

    # TODO: exec
    # TODO: ssh
    # TODO: Support surreal style for exec, ssh

    def exec_surreal(self, process_name, cmd, experiment_name=None):
        """
        kubectl exec -ti

        Args:
            component_name: can be agent-N, learner, ps, replay, tensorplex, tensorboard
            cmd: either a string command or a list of command args

        Returns:
            stdout string if is_print else None
        """
        if U.is_sequence(cmd):
            cmd = ' '.join(map(shlex.quote, cmd))
        if experiment_name is None:
            experiment_name = self.current_namespace()
        ns_cmd = self._get_ns_cmd(experiment_name)
        pod_name, container_name = self.get_pod_container(experiment_name, process_name)
        return self.run_raw(
            'exec -ti {} -c {} {} -- {}'.format(pod_name, container_name, ns_cmd, cmd)
        )


    def scp_surreal(self, src_file, dest_file, experiment_name=None):
        """
        https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#cp
        kurreal cp /my/local/file learner:/remote/file mynamespace
        is the same as
        kubectl cp /my/local/file mynamespace/nonagent:/remote/file -c learner
        """
        def _split(f):
            if ':' in f:
                process_name, path = f.split(':')
                return process_name, path
            else:
                return None, path
        if experiment_name is None:
            experiment_name = self.current_namespace()
        src_name, src_path = _split(src_file)
        dest_name, dest_path = _split(dest_file)
        assert (src_name is None) != (dest_name is None), \
            'one of "src_file" and "dest_file" must be remote and the other local.'
        container = src_container or dest_container  # at least one is None
        cmd = 'cp {} {}'.format(src_path, dest_path)
        if container:
            cmd += ' -c ' + container
        self.run_raw(cmd, print_cmd=True)

    def gcloud_get_config(self, config_key):
        """
        Returns: value of the gcloud config
        https://cloud.google.com/sdk/gcloud/reference/config/get-value
        for more complex outputs, add --format="json" to gcloud command
        """
        out, _, _ = self.run_verbose(
            'config get-value ' + config_key,
            print_out=False,
            raise_on_error=True,
            program='gcloud'
        )
        return out.strip()

    def gcloud_zone(self):
        """
        Returns: current gcloud zone
        """
        return self.gcloud_get_config('compute/zone')

    def gcloud_project(self):
        """
        Returns: current gcloud project
        https://cloud.google.com/sdk/gcloud/reference/config/get-value
        for more complex outputs, add --format="json" to gcloud command
        """
        return self.gcloud_get_config('project')

    def gcloud_configure_ssh(self):
        """
        Refresh the ssh settings for the current gcloud project
        populate SSH config files with Host entries from each instance
        https://cloud.google.com/sdk/gcloud/reference/compute/config-ssh
        """
        return self.run_raw('compute config-ssh', program='gcloud')

    def gcloud_url(self, node_name):
        """
        Returns: current gcloud project
        https://cloud.google.com/sdk/gcloud/reference/config/get-value
        for more complex outputs, add --format="json" to gcloud command
        """
        return '{}.{}.{}'.format(
            node_name, self.gcloud_zone(), self.gcloud_project()
        )

    def gcloud_ssh_node(self, node_name):
        """
        Don't forget to run gcloud_config_ssh() first
        """
        url = self.gcloud_url(node_name)
        return self.run_raw(
            'ssh -o StrictHostKeyChecking=no ' + url,
            program='',
            print_cmd=True
        )