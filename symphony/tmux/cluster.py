from symphony.engine import Cluster
from .experiment import TmuxExperimentSpec


class TmuxCluster(Cluster):
    def _new_experiment(self, *args, **kwargs):
        return TmuxExperimentSpec(*args, **kwargs)

    def launch(self, experiment_spec):
        print('launching', experiment_spec)
