from symphony_.engine import Cluster
from .experiment import TmuxExperimentSpec


class TmuxCluster(Cluster):
    def _new_experiment(self, *args, **kwargs):
        return TmuxExperimentSpec(*args, **kwargs)

    def launch(self):
        for e in self.experiments.values():
            print('launching', e)
