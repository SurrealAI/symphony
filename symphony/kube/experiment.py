from symphony.spec import ExperimentSpec
from .process import KubeProcessSpec
from .process_group import KubeProcessGroupSpec
from .builder import KubeIntraClusterService, KubeCloudExternelService
from symphony.utils.common import dump_yml
from symphony.engine.address_book import AddressBookData
import itertools


class KubeExperimentSpec(ExperimentSpec):
    def __init__(self, name, portrange=None):
        super().__init__(name)
        if portrange is None:
            portrange = list(range(7000,9000))
        self.portrange = portrange
        self.binded_services = {}
        self.exposed_services = {}

    def _new_process(self, *args, **kwargs):
        kwargs['standalone'] = True
        return KubeProcessSpec(*args, **kwargs)

    def _new_process_group(self, *args, **kwargs):
        return KubeProcessGroupSpec(*args, **kwargs)

    def compile(self):
        self.declare_services()
        self.assign_addresses()

        # print(self.process_groups['group'].pod_yml.yml())
        # exit(0)

        services = list(self.exposed_services.values()) + list(self.binded_services.values())
        pods = []
        for process_group in self.list_process_groups():
            pods.append(process_group)
        for process in self.list_processes():
            pods.append(process)

        components = services + pods
        
        return ''.join(['---\n' + x.yml() for x in components])

    def assign_addresses(self):
        ab_data = AddressBookData()
        for exposed_service_name in self.exposed_services:
            exposed_service = self.exposed_services[exposed_service_name]
            ab_data.add_entry(exposed_service.name, exposed_service_name, exposed_service.port)
        for binded_service_name in self.binded_services:
            binded_service = self.binded_services[binded_service_name]
            ab_data.add_entry(binded_service_name, binded_service_name, binded_service.port)
        env_dict = ab_data.dump()
        for process in self.list_all_processes():
            process.set_envs(env_dict)

    def declare_services(self):
        """
            Loop through all processes and assign addresses for all declared ports
        """
        for process in self.list_processes():
            if process.standalone:
                pod_yml = process.pod_yml
            else:
                pod_yml = process.parent_process_group.pod_yml
            for exposed_service_name in process.exposed_services:
                if exposed_service_name in self.exposed_services:
                    continue
                port = process.exposed_services[exposed_service_name]
                if port is None:
                    port = self.get_port()
                service = KubeCloudExternelService(exposed_service_name, port)
                pod_yml.add_label('service-' + exposed_service_name, 'expose')
                self.exposed_services[service.name] = service
            for binded_service_name in process.binded_services:
                if binded_service_name in self.binded_services:
                    continue
                port = process.binded_services[binded_service_name]
                if port is None:
                    port = self.get_port()
                service = KubeIntraClusterService(binded_service_name, port)
                pod_yml.add_label('service-' + binded_service_name, 'bind')
                self.binded_services[service.name] = service

    def get_port(self):
        if len(self.portrange) == 0:
            raise CompilationError('[Error] Experiment {} ran out of ports on Kubernetes.'.format(self.experiment.name))
        return self.portrange.pop()

    @classmethod
    def load_dict(cls):
        pass

    def dump_dict(self):
        pass
