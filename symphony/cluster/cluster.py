import subprocess as pc

def run_process(cmd):
    # if isinstance(cmd, str):  # useful for shell=False
    #     cmd = shlex.split(cmd.strip())
    proc = pc.Popen(cmd, stdout=pc.PIPE, stderr=pc.PIPE, shell=True)
    out, err = proc.communicate()
    return out.decode('utf-8'), err.decode('utf-8'), proc.returncode

class Cluster(object):
    """
        Represent the abstraction of a cluster on which we run experiments
    """
    def __init__(self):
        pass

    # TODO: define the interface
    def compile(self, experiment):
        """
            Base on the details specified by an experiment, 
            compile the launch plans
        """
        raise NotImplementedError
        experiment.compiled = True

    def launch(self, experiment, components=None):
        """
            Runs an compiled experiment
        Args:
            experiment: An experiment 
        """

    def kill(self, experiment_name, components=None):
        """
            Delete an experiment
        """

    def delete_multiple(self, *experiment_names):
        """
            Delete an experiment
        """

    def ls(self):
        """
            List all experiments 
        """

    def logs(self, experiment_name, process_name):
        """
            Retrieve logs from the process in the given experiment
        """

    def ssh(self, experiment_name, process_name):
        """
            ssh into the machine that contains process with process_name
        """

    def scp(self, experiment_name, process_name):
        """
            copy files from the machine that contains process with process_name
        """

# TODO: clean up the names maybe

if __name__ == "__main__":
    from symphony import ProcessConfig, ExperimentConfig, KubeCluster
    learner = ProcessConfig(name='learner', command='python', args='~/learner.py',
     kube_container_config='node-selector: surreal-agent\n', binds=['sampler_server'])
    agents = []
    for i in range(10):
        agent[i] = ProcessConfig(name='agent-{}'.format(i), command='python', args='~/agent.py', connects=['sampler_server'])
    experiment = ExperimentConfig(name='test-1')
    experiment.add_processes(learner, *agents)

    cluster = KubeCluster(init_args)
    cluster2 = TmuxCluster(init_args)
    cluster.launch(experiment)
    cluster2.launch(experiment)

    learner_2 = ProcessConfig(name='learner', command='python', args='~/learner.py',
     kube_container_config='node-selector: surreal-agent\n', binds=['sampler_server'])
    experiment.add_processes(learner_2)
    cluster.launch(experiment)