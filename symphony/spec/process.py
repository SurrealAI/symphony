from .base import BaseSpec


class ProcessSpec(BaseSpec):
    def __init__(self, name):
        super().__init__(name)
        self.parent_process_group = None
        self.parent_experiment = None

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
            raise ValueError('[Error] Process {} cannot be added to process_group {}. \
                It is already in process_group {}'.format(self.name,
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
            return {spec: None}
        if isinstance(spec, list) or isinstance(spec, tuple):
            return {x: None for x in spec}
        if isinstance(spec, dict):
            return spec

    # TODO: docs about bind/connect/connect input format
    def binds(self, spec):
        self.binded_services.update(self.parse_spec(spec))

    def connects(self, spec):
        self.connected_services.update(self.parse_spec(spec))

    def exposes(self, spec):
        self.exposed_services.update(self.parse_spec(spec))

    @classmethod
    def from_dict(cls):
        raise NotImplementedError

    def to_dict(self):
        raise NotImplementedError
