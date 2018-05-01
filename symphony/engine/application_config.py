import os
from os.path import expanduser
from pathlib import Path
from benedict.data_format import load_yaml_file, dump_yaml_file
from benedict import BeneDict


class _SymphonyConfigLoader(object):
    def __init__(self):
        self.load_global_settings()
        if 'SYMPH_CONFIG_FILE' in os.environ:
            config_path = expanduser(os.environ['SYMPH_CONFIG_FILE'])
        else:
            config_path = expanduser(self.global_settings.default_config)
        self.load_config(config_path)

    def default_config(self):
        return  {   
                    'cluster_name': 'default',
                    'cluster_type': 'kube',
                    'cluster_args': {
                        'dry_run': False,
                    },
                    'data_path': '~/.symphony/default',
                    'username': None,
                    'prefix_username': True,
                }

    def default_global_settings(self):
        return 

    def load_global_settings(self):
        """
        Loads symphony global config at ~/.symphony/meta
        """
        global_settings_path = os.environ.get('SYMPH_GLOBAL_SETTING', None)
        if global_settings_path is None:
            global_settings_path = '~/.symphony/settings.yml'
        global_settings_path = Path(expanduser(global_settings_path))
        global_settings_folder = global_settings_path.parent
        global_settings_folder.mkdir(exist_ok=True, parents=True)

        if not global_settings_path.exists():
            print('-------------------------------------')
            print('Global settings file not found')
            print('Generating default at {}'.format(str(global_settings_path)))
            print('Use SYMPH_GLOBAL_SETTING to specify another config to use')
            print('-------------------------------------')
            default_config_path = global_settings_folder / 'default_config.yml'
            default_settings = {
                'default_config': str(default_config_path)
            }
            dump_yaml_file(default_settings, str(global_settings_path))
            if not default_config_path.exists():
                print('-------------------------------------')
                print('Generating default config at {}'.format(str(default_config_path)))
                print('-------------------------------------')
                dump_yaml_file(self.default_config(), str(default_config_path))

        self.global_settings = BeneDict(load_yaml_file(str(global_settings_path)))

    def load_config(self, config_path):
        """
        Loads config specified by yaml file at config_path
        """
        if Path(expanduser(config_path)).exists():
            config = BeneDict(load_yaml_file(config_path))
        else:
            raise ValueError('No symphony config file found at {}'.format(config_path))
        self.cluster_name = config.cluster_name
        self.cluster_type = config.cluster_type
        self.cluster_args = config.cluster_args
        self.data_path = config.data_path
        self.username = config.username
        self.prefix_username = config.prefix_username

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