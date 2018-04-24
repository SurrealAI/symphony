import os
from pathlib import Path
from benedict import BeneDict

# TODO: make this configurable

class SymphonyConfigLoader(object):
    def __init__(self):
        local_config = None
        local_config_path = '.symphony.yml'
        if Path(local_config_path).exists():
            local_config = BeneDict.load_yaml_file(local_config_path)
        global_config = None
        if 'SYMPH_GLOBAL_CONFIG' in os.environ:
            global_config_path = os.environ['SYMPH_GLOBAL_CONFIG']
        else:
            global_config_path = os.path.expanduser('~/.symphony.yml')
        if Path(global_config_path).exists():
            global_config = BeneDict.load_yaml_file(global_config_path)

        self.apply_default_configs()
        if global_config:
            self.apply_configs(global_config)
        if local_config:
            self.apply_configs(local_config)
    
    def apply_default_configs(self):
        self.data_path = os.path.expanduser('~/symphony')
        self.username = None
        self.prefix_username = True

    def apply_configs(self, config):
        if 'data_directory' in config:
            self.data_path = os.path.expanduser(conf.data_path)
        if 'username' in config:
            self.experiment_name_prefix = config.username
        if 'prefix_username' in config:
            self.prefix_username = bool(config.prefix_username)

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
            SymphonyConfig.__instance = SymphonyConfigLoader()
        return SymphonyConfig.__instance