class ProcessConfig(object):
    def __init__(self, name, command=None, args=None, container_image=None, cluster_configs=None):

        self.name = name
        self.command = command
        self.args = args
        self.container_image = container_image
        if cluster_configs is None:
            cluster_configs = {}
        self.cluster_configs = cluster_configs
        self.process_group = None
        self.experiment = None
        self.provided_services = {}
        self.requested_services = {}
        self.exposed_services = {}
        self.reserved_ports = {}
        self.excecution_plan = {}

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

    # TODO: docs about bind/connect/connect input format
    def provides(self, *args, **kwargs):
        if self.compiled:
            print('[Warning] Process {} edited after being \
                compiled, there can be undefined behaviors'.format(self.name))
        for arg in args:
            self.provided_services[arg] = None
        for k in kwargs:
            self.provided_services[k] = kwargs[k]

    def requests(self, *args):
        if self.compiled:
            print('[Warning] Process {} edited after being \
                compiled, there can be undefined behaviors'.format(self.name))
        for arg in args:
            self.requested_services[arg] = None

    def exposes(self, *args, **kwargs):
        if self.compiled:
            print('[Warning] Process {} edited after being \
                compiled, there can be undefined behaviors'.format(self.name))
        for arg in args:
            self.exposed_services[arg] = None
        for k in kwargs:
            self.exposed_services[k] = kwargs[k]

    # TODO: define why reserves is necessary: Containers in a pod can have 
    # intra-container communication, want to avoid colliding with external
    def reserves(self, *args, **kwargs):
        if self.compiled:
            print('[Warning] Process {} edited after being \
                compiled, there can be undefined behaviors'.format(self.name))
        for arg in args:
            self.reserved_ports[arg] = None
        for k in kwargs:
            self.reserved_ports[k] = kwargs[k]

    @property
    # TODO: error checking
    def kube(self):
        return self.cluster_configs['kubernetes']
