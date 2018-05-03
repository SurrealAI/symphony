from symphony.commandline import SymphonyParser
from symphony.engine import *
from symphony.kube import *
import sys

class SymphonyDefaultParser(SymphonyParser):
    def create_cluster(self):
        return Cluster.new('kube')

def main():
    SymphonyDefaultParser().main()


    # self.load_global_settings()
    # if 'SYMPH_CONFIG_FILE' in os.environ:
    #     config_path = expanduser(os.environ['SYMPH_CONFIG_FILE'])
    # else:
    #     config_path = expanduser(self.global_settings.default_config)
    # self.load_config_file(config_path)



    # def default_config(self):
    #     return  {   
    #                 'data_path': '~/.symphony/default',
    #                 'username': None,
    #                 'prefix_username': True,
    #             }

    # def default_global_settings(self):
    #     return 

    # def load_global_settings(self):
    #     """
    #     Loads symphony global config at ~/.symphony/meta
    #     """
    #     global_settings_path = os.environ.get('SYMPH_GLOBAL_SETTING', None)
    #     if global_settings_path is None:
    #         global_settings_path = '~/.symphony/settings.yml'
    #     global_settings_path = Path(expanduser(global_settings_path))
    #     global_settings_folder = global_settings_path.parent
    #     global_settings_folder.mkdir(exist_ok=True, parents=True)

    #     if not global_settings_path.exists():
    #         print('-------------------------------------')
    #         print('Global settings file not found')
    #         print('Generating default at {}'.format(str(global_settings_path)))
    #         print('Use SYMPH_GLOBAL_SETTING to specify another config to use')
    #         print('-------------------------------------')
    #         default_config_path = global_settings_folder / 'default_config.yml'
    #         default_settings = {
    #             'default_config': str(default_config_path)
    #         }
    #         dump_yaml_file(default_settings, str(global_settings_path))
    #         if not default_config_path.exists():
    #             print('-------------------------------------')
    #             print('Generating default config at {}'.format(str(default_config_path)))
    #             print('-------------------------------------')
    #             dump_yaml_file(self.default_config(), str(default_config_path))

    #     self.global_settings = BeneDict(load_yaml_file(str(global_settings_path)))

    # def load_config_file(self, config_path):
    #     """
    #     Loads config specified by yaml file at config_path
    #     """
    #     if Path(expanduser(config_path)).exists():
    #         config = BeneDict(load_yaml_file(config_path))
    #         self.load_config(config)
    #     else:
    #         raise ValueError('No symphony config file found at {}'.format(config_path))

    # def load_config(self, config):
    #     config = BeneDict(config)
    #     self.cluster_name = config.cluster_name
    #     self.cluster_type = config.cluster_type
    #     self.cluster_args = config.cluster_args
    #     self.data_path = config.data_path
    #     self.username = config.username
    #     self.prefix_username = config.prefix_username


    # def main():
    #     # Create a parser with symphony related subparsers
    #     master_parser, subparsers, claimed_commands = create_symphony_parser()
    #     # or claimed_commands = add_symphony_parser(subparsers)
        
    #     # optionally add your own subparsers
    #     subparsers.add_parser('nothing', help='does nothing')

    #     args, _ = symph_parse_args(master_parser)
    #     # args, argv = symph_parse_args(master_parser)

    #     is_symph = symph_exec_args(args)
    #     if not is_symph:
    #         print('called nothing')
    #         print('claimed commands', claimed_commands)


    # class DQNParser(SymphParser):
    #     # expose create cluster
    #     # use case 1: create a new subcommand parser
    #     def setup(self):
    #         super().setup()
    #         # 
    #         parser = self._add_subparser('delete', aliases=['d'])
    #         self._add_experiment_name(parser, required=False, positional=True)
    #         parser.add_argument(
    #             '-f', '--force',
    #             action='store_true',
    #             help='force delete, do not show confirmation message.'
    #         )
    #         parser = self._add_subparser('delete', aliases=['d'])
    #         self._add_experiment_name(parser, required=False, positional=True)
    #         parser.add_argument(
    #             '-f', '--force',
    #             action='store_true',
    #             help='force delete, do not show confirmation message.'
    #         )
    #         parser = self._add_subparser('delete', aliases=['d'])
    #         self._add_experiment_name(parser, required=False, positional=True)
    #         parser.add_argument(
    #             '-f', '--force',
    #             action='store_true',
    #             help='force delete, do not show confirmation message.'
    #         )

    #     def setup_create(self, parser, arg):
    #         # enable `symphony create -f -a`
    #         parser.add_argument('-f', 'file_system')
    #         parser.add_argument('-a', store_action=True)
    #         return parser

    #     def action_create(self, args):
    #         self.cluster.run_create(*args)    

    #     # use case 2, override default symphony cmdline behavior
    #     def action_log(self, args):
    #         print('my extra banner')
    #         super().action_log(args)


    # # TODO: doc about how to install it as commandline script
    # DQNParser().main()


if __name__ == '__main__':
    main()
    # SymphonyConfig().set_config({'save_path': })
