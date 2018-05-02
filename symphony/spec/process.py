from .base import BaseSpec
from symphony.utils.common import check_valid_dns


class ProcessSpec(BaseSpec):
    def __init__(self, name):
        super().__init__(name)
        self.parent_process_group = None
        self.parent_experiment = None
        self.binded_services = {}
        self.connected_services = {}
        self.exposed_services = {}

    def _set_experiment(self, experiment):
        """ Internal method
            Set process to belong to experiment
        """
        if self.parent_experiment is not None:
            raise ValueError('[Error] Process {} cannot be added to experiment {}. \
                It is already in experiment {}'.format(self.name,
                                                        experiment.name,
                                                        self.parent_experiment.name))
        self.parent_experiment = experiment

    def _set_process_group(self, process_group):
        """ Internal method
            Set process to belong to process_group
        """
        if self.parent_process_group is not None:
            raise ValueError('[Error] Process {} cannot be added to process_group {}. ' \
                'It is already in process_group {}'.format(self.name,
                                                        process_group.name,
                                                        self.parent_process_group.name))
        self.parent_process_group = process_group

    def parse_spec(self, spec):
        """
            Compiles port specification, it can be (tested in this order): 
            (str): arrange an arbitrary port for this service
            (list(str)):arrange an arbitrary port for every string in the list
            (dict): for 'k','v' in dict: arrange port 'v' for service 'k'
        """
        if isinstance(spec, str):
            check_valid_dns(spec)
            return {spec: None}
        if isinstance(spec, list) or isinstance(spec, tuple):
            for x in spec:
                check_valid_dns(x)
            return {x: None for x in spec}
        if isinstance(spec, dict):
            for x in spec:
                check_valid_dns(x)
            return spec

    # TODO: docs about bind/connect/expose input format
    def binds(self, spec):
        self.binded_services.update(self.parse_spec(spec))

    def connects(self, spec):
        self.connected_services.update(self.parse_spec(spec))

    def exposes(self, spec):
        self.exposed_services.update(self.parse_spec(spec))

    @classmethod
    def load_dict(cls, di):
        """
        For creating new instances
        """
        instance = cls(di['name'])
        instance._load_dict(di)
        return instance

    def _load_dict(self, di):
        """
        Loads information from di, can be inherited
        """
        self.binded_services = di['binded_services']
        self.connected_services = di['connected_services']
        self.exposed_services = di['exposed_services']

    def dump_dict(self):
        di = {'name': self.name}
        di['binded_services'] = self.binded_services
        di['connected_services'] = self.connected_services
        di['exposed_services'] = self.exposed_services
        return di
