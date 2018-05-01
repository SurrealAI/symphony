from symphony.commandline import *
import sys

def main():
    # Create a parser with symphony related subparsers
    master_parser, subparsers, claimed_commands = create_symphony_parser()
    # or claimed_commands = add_symphony_parser(subparsers)
    
    # optionally add your own subparsers
    subparsers.add_parser('nothing',help='does nothing')

    args, _ = symph_parse_args(master_parser)
    # args, argv = symph_parse_args(master_parser)

    is_symph = symph_exec_args(args)
    if not is_symph:
        print('called nothing')
        print('claimed commands', claimed_commands)

if __name__ == '__main__':
    main() 
