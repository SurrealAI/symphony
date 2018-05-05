from symphony.engine import SymphonyConfig
from symphony.spec import ExperimentSpec
from benedict.data_format import dump_yaml_str, load_yaml_file
from pathlib import Path
from os.path import expanduser
import os
import pickle


class LocalFileManager:
    def __init__(self):
        folder = SymphonyConfig().experiment_folder
        if folder:
            self.data_root = Path(expanduser(folder))
        else:
            self.data_root = None

    def has_experiment_folder(self):
        return (self.data_root is not None)

    def experiment_path(self, experiment_name):
        experiment_path = self.data_root / experiment_name
        experiment_path.mkdir(exist_ok=True, parents=True)
        return experiment_path

    def experiment_exists(self, experiment_name):
        return self.experiment_file(experiment_name).exists()

    def experiment_file(self, experiment_name):
        experiment_file = self.experiment_path(experiment_name) / 'experiment.yaml'
        return str(experiment_file)

    def load_experiment(self, experiment_name):
        experiment_file = Path(self.experiment_file(experiment_name))
        if experiment_file.exists():
            experiment = ExperimentSpec.load_dict(load_yaml_file(str(experiment_file)))
        else:
            raise ValueError('[Error] Cannot find experiment {}'.format(experiment_name))
        return experiment

    def save_experiment(self, experiment):
        assert isinstance(experiment, ExperimentSpec)
        experiment_name = experiment.name
        experiment_file = Path(self.experiment_file(experiment_name))
        di = experiment.dump_dict()
        with experiment_file.open('w') as f:
            f.write(dump_yaml_str(di))
        return str(experiment_file)

