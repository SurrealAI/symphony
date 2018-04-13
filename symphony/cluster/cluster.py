class CompilationError(Exception):
    pass

class Cluster(object):
    """
        Represent the abstraction of a cluster on which we run experiments
    """
    def __init__(self):
        pass

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

    def run(self, cmd, program):
        cmd = program + ' ' + cmd
        if self.dry_run:
            print(cmd)
            return '', '', 0
        else:
            out, err, retcode = run_process(cmd)
            if 'could not find default credentials' in err:
                print("Please try `gcloud container clusters get-credentials mycluster` "
                      "to fix credential error")
            return out.strip(), err.strip(), retcode


    def run_raw(self, cmd, program, print_cmd=False):
        """
        Raw os.system calls

        Returns:
            error code
        """
        cmd = program + ' ' + cmd
        if self.dry_run:
            print(cmd)
        else:
            if print_cmd:
                print(cmd)
            return os.system(cmd)

    def _print_err_return(self, out, err, retcode):
        print_err('error code:', retcode)
        print_err('*' * 20, 'stderr', '*' * 20)
        print_err(err)
        print_err('*' * 20, 'stdout', '*' * 20)
        print_err(out)
        print_err('*' * 46)


    def run_verbose(self, cmd,
                    print_out=True,
                    raise_on_error=False,
                    program='kubectl'):
        out, err, retcode = self.run(cmd, program=program)
        if retcode != 0:
            self._print_err_return(out, err, retcode)
            msg = 'Command `{} {}` fails'.format(program, cmd)
            if raise_on_error:
                raise RuntimeError(msg)
            else:
                print_err(msg)
        elif out and print_out:
            print(out)
        return out, err, retcode



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