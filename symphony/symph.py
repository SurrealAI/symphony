from symphony.commandline import SymphonyCommandLine
import sys

def main():
    SymphonyCommandLine().main()

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
