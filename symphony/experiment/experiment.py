from symphony.experiment.process import ProcessConfig
from symphony.experiment.process_group import ProcessGroupConfig
from symphony.cluster.kubecluster import KubeExperiment
from symphony.core.application_config import SymphonyConfig

class ExperimentConfig(object):
    """
        This class holds all information about what process you want to run
        and how you want to run each of them.
    """
    def __init__(self, name, cluster_configs=None, use_global_name_prefix=True):
        self.name = name
        if use_global_name_prefix and SymphonyConfig.experiment_name_prefix is not None:
            self.name = SymphonyConfig.experiment_name_prefix + '-' + self.name
        self.processes = {}
        self.process_groups = {}
        self.excecution_plan = {}
        if cluster_configs is None:
            cluster_configs = {}
        self.cluster_configs = cluster_configs
        self.compiled = False

    def add_process(self, *processes):
        if self.compiled:
            print('[Warning] Experiment {} edited after being \
                compiled, there can be undefined behaviors'.format(self.name))
        for process in processes:
            assert(isinstance(process, ProcessConfig))
            process_name = process.name
            if process_name in self.processes:
                raise ValueError('[Error] Cannot add process {} to experiment \
                {}: a process with the same name already exists'.format(process_name, self.name))
            self.processes[process_name] = process
            process._set_experiment(self)

    def add_process_group(self, *process_groups):
        if self.compiled:
            print('[Warning] Experiment {} edited after being \
                compiled, there can be undefined behaviors'.format(self.name))
        for process_group in process_groups:
            assert(isinstance(process_group, ProcessGroupConfig))
            process_group_name = process_group.name
            if process_group_name in self.process_groups:
                raise ValueError('[Error] Cannot add process group {} to experiment \
                {}: a process group with the same name already exists'.format(process_group_name, self.name))
            self.process_groups[process_group_name] = process_group
            process_group._set_experiment(self)

    def use_kube(self):
        """
            Initialize kubernetes related configs on one-self
        """
        k8sconfig = KubeExperiment(self)
        k8sconfig.initialize_configs()

    @property
    # TODO: error checking
    def kube(self):
        return self.cluster_configs['kubernetes']

# process_a = Process(name='learner', binds=['sampler_backend'], connects=['sampler_backend'])
# process_b = Process(name='replay', connects=['sampler_backend'])
# pg = ProcessGroup()
# pg.add_process(process_a)
# pg.add_process(process_b)
# exp = Experiment(use_addressbook=True)
# exp.use_addressbook()
# experiment.add_process(process_a)
# experiment.add_process(process_b)
# experiment.add_process_group('learner', 'reply')

# exp.add_process('name')
