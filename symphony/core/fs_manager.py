from symphony.core.application_config import SymphonyConfig
from symphony.experiment.experiment import ExperimentConfig
from pathlib import Path
import os
import pickle


# TODO: no one can read pickle, can we make it better?

class FSManager(object):
    def __init__(self):
        self.data_root = Path(SymphonyConfig().data_path)

    def experiment_path(self, experiment_name):
        experiment_path = self.data_root / experiment_name
        experiment_path.mkdir(exist_ok=True)
        return experiment_path

    def experiment_file(self, experiment_name):
        experiment_file = self.experiment_path(experiment_name) / 'experiment.pickle'
        return experiment_file

    def launch_plan_file(self, experiment_name, cluster_type):
        """
            Generates a filename to save launch_plan. TODO: shall we make it timestamped
        """
        return self.experiment_path(experiment_name) / cluster_type

    def load_experiment(self, experiment_name):
        experiment_file = self.experiment_file(experiment_name)
        if experiment_file.exists():
            with open(experiment_file, 'rb') as f:
                experiment = pickle.load(f)
        else:
            raise ValueError('[Error] Cannot find experiment {}'.format(experiment_name))
        assert isinstance(experiment, ExperimentConfig)
        return experiment

    def save_experiment(self, experiment):
        assert isinstance(experiment, ExperimentConfig)
        experiment_name = experiment.name
        experiment_file = self.experiment_file(experiment_name)
        with open(experiment_file, 'wb') as f:
            experiment = pickle.dump(experiment, f)
        return experiment_file

    def save_launch_plan(self, experiment_name, launch_plan, cluster_type):
        launch_plan_file = self.launch_plan_file(experiment_name, cluster_type)
        with open(launch_plan_file, 'w') as f:
            f.write(launch_plan)
        return launch_plan_file

