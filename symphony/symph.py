from symphony.commandline import SymphonyParser
import sys

def main():
    parser = SymphonyParser().setup_master()
    assert sys.argv.count('--') <= 1, \
        'command line can only have at most one "--"'
    if '--' in sys.argv:
        idx = sys.argv.index('--')
        remainder = sys.argv[idx+1:]
        sys.argv = sys.argv[:idx]
        has_remainder = True  # even if remainder itself is empty
    else:
        remainder = []
        has_remainder = False
        
    args = parser.parse_args()
    args.remainder = remainder
    args.has_remainder = has_remainder
    args.func(args)


if __name__ == '__main__':
    main() 
