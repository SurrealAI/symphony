from symphony.spec import ExperimentSpec
from .process import KubeProcessSpec
from .process_group import KubeProcessGroupSpec
from .builder import KubeIntraClusterService, KubeCloudExternelService
from symphony.utils.common import dump_yml
from symphony.engine.address_book import AddressBookData
import copy
import itertools


class KubeExperimentSpec(ExperimentSpec):
    _ProcessClass = KubeProcessSpec
    _ProcessGroupClass = KubeProcessGroupSpec

    def __init__(self, name, portrange=None):
        super().__init__(name)
        if portrange is None:
            portrange = list(range(7000,9000))
        self.portrange = portrange
        self.binded_services = {}
        self.exposed_services = {}

    def _compile(self):
        self.declare_services()
        self.assign_addresses()

        components = {}

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
        exposed = {}
        binded = {}
        portrange = copy.deepcopy(self.portrange)
        for process in self.list_all_processes():
            if process.standalone:
                pod_yml = process.pod_yml
            else:
                pod_yml = process.parent_process_group.pod_yml

            for exposed_service_name in process.exposed_services:
                pod_yml.add_label('service-' + exposed_service_name, 'expose')
                port = process.exposed_services[exposed_service_name]
                exposed[exposed_service_name] = port
                if port in self.portrange:
                    portrange.remove(port)

            for binded_service_name in process.binded_services:
                pod_yml.add_label('service-' + binded_service_name, 'bind')
                port = process.binded_services[binded_service_name]
                binded[binded_service_name] = port
                if port in self.portrange:
                    portrange.remove(port)                

        for exposed_service_name, port in exposed.items():
            if port is None:
                port = self.get_port(portrange)
            service = KubeCloudExternelService(exposed_service_name, port)
            self.exposed_services[service.name] = service
        for binded_service_name, port in binded.items():
            if port is None:
                port = self.get_port(portrange)
            service = KubeIntraClusterService(binded_service_name, port)
            self.binded_services[service.name] = service

    def get_port(self, portrange):
        if len(portrange) == 0:
            raise CompilationError('[Error] Experiment {} ran out of ports on Kubernetes.'.format(self.experiment.name))
        return portrange.pop(0)

    def _load_dict(self, di):
        super()._load_dict(di)
        self.portrange = compact_range_loads(di['portrange'])

    def dump_dict(self):
        di = super().dump_dict()
        di['portrange'] = compact_range_dumps(self.portrange)
        return di

def compact_range_dumps(li):
    """
    Accepts a list of integers and represent it as intervals
    [1,2,3,4,6,7] => '1-4,6-7'
    """
    li = sorted(li)
    low = None
    high = None
    collections = []
    for i in range(len(li)):
        number = li[i]
        if low is None:
            low = number
            high = number
        elif high + 1 == number:
            high = number
        else:
            collections.append('{}-{}'.format(low,high))
            low = None
            high = None
    collections.append('{}-{}'.format(low,high))
    return ','.join(collections)

def compact_range_loads(s):
    specs = [x.split('-') for x in s.split(',')]
    li = []
    for low, high in specs:
        li += list(range(int(low), int(high)))
    return li
