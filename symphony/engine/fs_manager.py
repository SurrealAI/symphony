from symphony.core.application_config import SymphonyConfig
from symphony.spec import ExperimentSpec
from benedict.data_format import dump_yaml_string, load_yaml_file
from pathlib import Path
from os.path import expanduser
import os
import pickle


class FSManager(object):
    def __init__(self):
        self.data_root = Path(expanduser(SymphonyConfig().data_path))

    def experiment_path(self, experiment_name):
        experiment_path = self.data_root / experiment_name
        experiment_path.mkdir(exist_ok=True, parents=True)
        return experiment_path

    def experiment_file(self, experiment_name):
        experiment_file = self.experiment_path(experiment_name) / 'experiment.yaml'
        return experiment_file

    def load_experiment(self, experiment_name):
        experiment_file = self.experiment_file(experiment_name)
        if experiment_file.exists():
            experiment = ExperimentSpec.load_dict(load_yaml_file(str(experiment_file)))
        else:
            raise ValueError('[Error] Cannot find experiment {}'.format(experiment_name))
        return experiment

    def save_experiment(self, experiment):
        assert isinstance(experiment, ExperimentConfig)
        experiment_name = experiment.name
        experiment_file = self.experiment_file(experiment_name)
        di = experiment.dump_dict()
        with experiment_file.open('wb') as f:
            f.write(dump_yaml_string(di))
        return str(experiment_file)

