from symphony.utils.common import print_err
from os.path import expanduser
from pathlib import Path
from benedict.data_format import load_yaml_file, dump_yaml_file, load_json_file
from benedict import BeneDict


class _SymphonyConfigLoader:
    def __init__(self):
        self.registry = {}
        self.register_handler('experiment_folder', str)
        self.register_handler('username', str)

    def register_handler(self, field, handler):
        """
        Registers 
        """
        if field in self.registry:
            raise ValueError('Field {} is already registered in SymphonyConfig'.format(field))
        self.registry[field] = handler
        setattr(self, field, None)

    def set_username(self, name):
        """
        Set username so every experiment is automatically prefixed by this username
        Args:
            name: string to prepend to every experiment
        """
        self.update({'username': name})

    def set_experiment_folder(self, folder):
        """
        Set the folder so that every experiment is saved to a subdirectory under the folder
        Args:
            folder: location to save all experiments
        """
        self.update({'experiment_folder': folder})

    def load_config_file(self, file):
        if file.find('.json'):
            self.update(load_json_file(file))
        else:
            self.update(load_yaml_file(file))

    def update(self, di):
        keys = di.keys()
        for key, val in di.items():
            if key in self.registry:
                setattr(self, key, self.registry[key](di[key]))
            else:
                print_err("[Warning] Key {} unrecognized by symphony config, ignored.".format(key))


class SymphonyConfig:
    """
        Reads the path to symphony config yml file. 
        Order is 
            ./.symphony.yml
            SYMPH_GLOBAL_CONFIG
            ~/.symphony.yml
    """
    _instance = None
    def __new__(cls): # __new__ always a classmethod
        if not SymphonyConfig._instance:
            SymphonyConfig._instance = _SymphonyConfigLoader()
        return SymphonyConfig._instance

    @classmethod
    def reset(cls):
        SymphonyConfig._instance = _SymphonyConfigLoader()
