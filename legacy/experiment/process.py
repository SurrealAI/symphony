from symphony.utils.common import sanitize_name


class ProcessConfig(object):
    def __init__(self, name, command=None, args=None, container_image=None, cluster_configs=None):
        self.name = sanitize_name(name)
        self.command = command
        self.args = args
        self.container_image = container_image
        if cluster_configs is None:
            cluster_configs = {}
        self.cluster_configs = cluster_configs
        self.process_group = None
        self.experiment = None
        self.binded_services = {}
        self.connected_services = {}
        self.exposed_services = {}
        self.reserved_ports = {}

        self.compiled = False

    def _set_experiment(self, experiment):
        """ Internal method
            Set process to belong to experiment
        """
        if self.experiment is not None:
            raise ValueError('[Error] Process {} cannot be added to experiment {}. \
                It is already in experiment {}'.format(self.name,
                                                        experiment.name, self.experiment.name))
        self.experiment = experiment

    def _set_process_group(self, process_group):
        """ Internal method
            Set process to belong to process_group
        """
        if self.process_group is not None:
            raise ValueError('[Error] Process {} cannot be added to process_group {}. \
                It is already in process_group {}'.format(self.name,
                                                        process_group.name, self.process_group.name))
        self.process_group = process_group

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
        if self.compiled:
            print('[Warning] Process {} edited after being \
                compiled, there can be undefined behaviors'.format(self.name))
        self.binded_services.update(self.parse_spec(spec))

    def connects(self, spec):
        if self.compiled:
            print('[Warning] Process {} edited after being \
                compiled, there can be undefined behaviors'.format(self.name))
        self.connected_services.update(self.parse_spec(spec))

    def exposes(self, spec):
        if self.compiled:
            print('[Warning] Process {} edited after being \
                compiled, there can be undefined behaviors'.format(self.name))
        self.exposed_services.update(self.parse_spec(spec))

    # # TODO: define why reserves is necessary: Containers in a pod can have 
    # # intra-container communication, want to avoid colliding with external
    # def reserves(self, *args, **kwargs):
    #     if self.compiled:
    #         print('[Warning] Process {} edited after being \
    #             compiled, there can be undefined behaviors'.format(self.name))
    #     for arg in args:
    #         self.reserved_ports[arg] = None
    #     for k in kwargs:
    #         self.reserved_ports[k] = kwargs[k]

    @property
    # TODO: error checking
    def kube(self):
        return self.cluster_configs['kubernetes']
