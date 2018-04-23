from symphony_.engine import Cluster
from .experiment import KubeExperimentSpec


class KubeCluster(Cluster):
    def _new_experiment(self, *args, **kwargs):
        return KubeExperimentSpec(*args, **kwargs)

    def launch(self, experiment_spec):
        print('launching', experiment_spec)

