from symphony.engine import Cluster
from .experiment import KubeExperimentSpec


class KubeCluster(Cluster):
    def __init__(self, dry_run=False):
        self.dry_run = dry_run

    def new_experiment(self, *args, **kwargs):
        return KubeExperimentSpec(*args, **kwargs)

    def launch(self, experiment_spec):
        print('launching', experiment_spec)
        launch_plan = experiment_spec.compile()

        if self.dry_run:
            print(launch_plan)
        else:
            self.set_namespace(experiment.name)
            self.fs.save_experiment(experiment)
            launch_plan_file = self.fs.save_launch_plan(experiment.name, launch_plan, 'kubernetes')
            #TODO: persist yaml file
            cmdline.run_verbose('kubectl create namespace ' + experiment.name, dry_run=self.dry_run)
            cmdline.run_verbose('kubectl create -f "{}" --namespace {}'.format(launch_plan_file, experiment.name), dry_run=self.dry_run)
    

