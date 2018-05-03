import os
from os.path import expanduser
from pathlib import Path
from benedict.data_format import load_yaml_file, dump_yaml_file
from benedict import BeneDict


class _SymphonyConfigLoader(object):
    def __init__(self):
        self.experiment_folder = None
        self.username = None

    def set_username(self, name):
        """
        Set username so every experiment is automatically prefixed by this username
        Args:
            name: string to prepend to every experiment
        """
        self.username = name

    def set_experiment_folder(self, folder):
        """
        Set the folder so that every experiment is saved to a subdirectory under the folder
        Args:
            folder: location to save all experiments
        """
        self.experiment_folder = folder


class SymphonyConfig(object):
    """
        Reads the path to symphony config yml file. 
        Order is 
            ./.symphony.yml
            SYMPH_GLOBAL_CONFIG
            ~/.symphony.yml
    """
    __instance = None
    def __new__(cls): # __new__ always a classmethod
        if not SymphonyConfig.__instance:
            SymphonyConfig.__instance = _SymphonyConfigLoader()
        return SymphonyConfig.__instance