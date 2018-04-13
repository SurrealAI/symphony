from symphony.experiment.process import ProcessConfig

class ProcessGroupConfig(object):
    def __init__(self, name, cluster_configs=None):
        self.name = name
        if cluster_configs is None:
            cluster_configs = {}
        self.cluster_configs = cluster_configs
        self.processes = {}
        self.excecution_plan = {}
        self.experiment = None
        self.compiled = False

    def add_process(self, *processes):
        if self.compiled:
            print('[Warning] Process group {} edited after being \
                compiled, there can be undefined behaviors'.format(self.name))
        for process in processes:
            assert(isinstance(process, ProcessConfig))
            self.processes[process.name] = process
            process._set_process_group(self)
            if self.experiment is not None:
                self.experiment.add_process(process)

    def _set_experiment(self, experiment):
        """ Internal method
            Set process to belong to experiment
        """
        if self.experiment is not None:
            raise ValueError('[Error] Process group {} cannot be added to experiment {}. \
                It is already in experiment {}'.format(self.name,
                                                        experiment.name, self.experiment.name))
        self.experiment = experiment
        for process in self.processes.values():
            experiment.add_process(process)
