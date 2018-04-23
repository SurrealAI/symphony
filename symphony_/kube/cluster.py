from symphony_.engine import Cluster
from .experiment import KubeExperimentSpec


class KubeCluster(Cluster):
    def _new_experiment(self, *args, **kwargs):
        return KubeExperimentSpec(*args, **kwargs)

    def launch(self):
        for e in self.experiments.values():
            print('launching', e)
