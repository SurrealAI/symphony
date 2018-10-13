import copy
from symphony.spec import ExperimentSpec
from symphony.engine.address_book import AddressBook
from symphony.utils.common import compact_range_dumps, compact_range_loads
from symphony.utils.common import sanitize_name_kubernetes
from .process import KubeProcessSpec
from .process_group import KubeProcessGroupSpec
from .builder import (
    KubeIntraClusterService,
    KubeCloudExternelService,
    KubeSecret
    )


class KubeExperimentSpec(ExperimentSpec):
    _ProcessClass = KubeProcessSpec
    _ProcessGroupClass = KubeProcessGroupSpec

    def __init__(self,
                 name,
                 port_range=None,
                 secrets=None):
        """
        Creates an experiment on kubernetes

        Args:
            name: name of experiments
            port_range: range of port numbers to assign (default: 7000-9000)
            secrets: list of files to mount as secrets (default: {None})
        """
        name = sanitize_name_kubernetes(name)
        super().__init__(name)
        if port_range is None:
            port_range = list(range(7000, 9000))
        if secrets is None:
            secrets = []
        self.port_range = port_range
        self.binded_services = {}
        self.exposed_services = {}
        self.secrets = secrets

    def _compile(self):
        self.address_book = AddressBook()

        self.declare_services()
        self.assign_addresses()
        secrets = self.add_secret()

        components = {}
        if secrets is not None:
            components['secrets'] = secrets.yml()
        for k, v in self.exposed_services.items():
            components['exposed-service-' + k] = v.yml()
        for k, v in self.binded_services.items():
            components['binded-service-' + k] = v.yml()

        for process_group in self.list_process_groups():
            components['process-group-' + process_group.name] = process_group.yml()
        for process in self.list_processes():
            components['process-' + process.name] = process.yml()

        return components

    def compile(self):
        components = self._compile()
        return ''.join(['---\n' + x for x in components.values()])

    def assign_addresses(self):
        for exposed_service_name in self.exposed_services:
            exposed_service = self.exposed_services[exposed_service_name]
            self.address_book.add_entry(exposed_service.name,
                                        exposed_service.name,
                                        exposed_service.port)
        for binded_service_name in self.binded_services:
            binded_service = self.binded_services[binded_service_name]
            self.address_book.add_entry(binded_service.name,
                                        binded_service.name,
                                        binded_service.port)
        env_dict = self.address_book.dump()
        for process in self.list_all_processes():
            process.set_envs(env_dict)

    def declare_services(self):
        """
            Loop through all processes and assign addresses for all declared ports
        """
        exposed = {}
        binded = {}
        port_range = copy.deepcopy(self.port_range)
        for process in self.list_all_processes():
            if process.standalone:
                pod_yml = process.pod_yml
            else:
                pod_yml = process.parent_process_group.pod_yml

            for exposed_service_name in process.exposed_services:
                pod_yml.add_label('service-' + exposed_service_name, 'expose')
                port = process.exposed_services[exposed_service_name]
                exposed[exposed_service_name] = port
                if port in self.port_range:
                    port_range.remove(port)

            for binded_service_name in process.binded_services:
                pod_yml.add_label('service-' + binded_service_name, 'bind')
                port = process.binded_services[binded_service_name]
                binded[binded_service_name] = port
                if port in self.port_range:
                    port_range.remove(port)

        for exposed_service_name, port in exposed.items():
            if port is None:
                port = self.get_port(port_range)
            service = KubeCloudExternelService(exposed_service_name, port)
            self.exposed_services[service.name] = service
        for binded_service_name, port in binded.items():
            if port is None:
                port = self.get_port(port_range)
            service = KubeIntraClusterService(binded_service_name, port)
            self.binded_services[service.name] = service
        self.validate_connect()

    def add_secret(self):
        default_secret_name = 'symph-default-secret'
        if len(self.secrets) > 0:
            for process in self.list_all_processes():
                process.mount_secret(secret_name=default_secret_name,
                                     mount_path='/etc/secrets')
            return KubeSecret.from_files(
                        default_secret_name,
                        files=self.secrets)
        else:
            return None

    def validate_connect(self):
        """
        Check if all connected services are correctly provided
        """
        for process in self.list_all_processes():
            for connected_service_name in process.connected_services:
                if connected_service_name not in self.binded_services:
                    raise ValueError('Service {} is connected by process {} but not binded' \
                                     .format(connected_service_name, process.name))

    def get_port(self, port_range):
        if len(port_range) == 0:
            raise ValueError('[Error] Experiment {} ran out of ports on Kubernetes.' \
                             .format(self.name))
        return port_range.pop(0)

    def _load_dict(self, di):
        super()._load_dict(di)
        self.port_range = compact_range_loads(di['port_range'])
        self.secrets = di['secrets']

    def dump_dict(self):
        data = super().dump_dict()
        data['port_range'] = compact_range_dumps(self.port_range)
        data['secrets'] = self.secrets
        return data
