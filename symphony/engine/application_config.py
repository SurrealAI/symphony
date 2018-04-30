import os
from pathlib import Path
from benedict.data_format import load_yaml_file, dump_yaml_file
from benedict import BeneDict


class SymphonyConfigLoader(object):
    def __init__(self):
        config = None
        if 'SYMPH_GLOBAL_CONFIG' in os.environ:
            config_path = os.environ['SYMPH_GLOBAL_CONFIG']
        else:
            config_path = os.path.expanduser('~/.symphony.yml')
        self.config_path = config_path

        if Path(config_path).exists():
            config = BeneDict(load_yaml_file(config_path))
        else:
            print('-------------------------------------')
            print('No symphony config file found')
            print('Generating default at {}'.format(config_path))
            print('Use SYMPH_GLOBAL_CONFIG to specify another config to use')
            print('-------------------------------------')
            config = BeneDict(self.default_config())
            config.dump_yaml_file(config_path)

        if 'SYMPH_CURRENT_CLUSTER' in os.environ:
            current_cluster = os.environ['SYMPH_CURRENT_CLUSTER']
        else:
            current_cluster = config.default_cluster

        if not current_cluster in config.clusters:
            raise ValueError('Currently activated cluster {} undefined. Please check your config file'.format(current_cluster))

        self.all_config = config
        self.config = config.clusters[current_cluster]
        self.load(self.config)

    def default_config(self):
        return {
            'default_cluster': 'default',
            'clusters': {
                'default': {
                    'type': 'kube',
                    'args': {
                        'dry_run': False,
                    },
                    'data_path': '~/symphony_default',
                    'username': None,
                    'prefix_username': True,
                }
            }
        }

    def load(self, config):
        self.cluster_type = config.type
        self.cluster_args = config.args
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
            SymphonyConfig.__instance = SymphonyConfigLoader()
        return SymphonyConfig.__instance