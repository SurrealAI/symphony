from symphony.engine import *
from symphony.kube import *
from symphony.utils.common import print_err, sanitize_name
import webbrowser
import argparse
import re
import sys


def sanitize_experiment_name(name):
    """
        Allows None through so that kubecluster will use default name instead
        TODO: update when tmux is in the picture
    """
    if name is None:
        return name
    else:
        return sanitize_name(name)


class SymphonyCommandLine(object):
    def __init__(self, subparsers):
        """
        This class adds parsers to sub_parser
        Args:
            sub_parser(generate by argparse.ArgumentParser().add_subparsers())
        """
        subparsers.required = True
        self._subparsers = subparsers

        config = SymphonyConfig()
        self.cluster = Cluster.new(config.cluster_type, **config.cluster_args)
        self.claimed_commands = set()

        self.setup()

    # ======================================================
    # ==================== Parser setup ====================
    # ======================================================
    def setup(self):
        """
        Main function that returns the configured parser
        """
        # Action api
        self._setup_delete() #
        self._setup_delete_batch() # 
        self._setup_scp() #
        self._setup_ssh() # 
        self._setup_exec() #
        # Query api
        self._setup_list_experiments() #
        self._setup_experiment() #
        self._setup_process() # 
        self._setup_log() #
        self._setup_visit() #

    def _add_subparser(self, name, aliases, **kwargs):
        self.claimed_commands.add(name)
        for alias in aliases:
            self.claimed_commands.add(alias)
        method_name = 'symphony_' + name.replace('-', '_')
        method_func = getattr(self, method_name)  # Symphony.symphony_create()

        parser = self._subparsers.add_parser(
            name,
            help=method_func.__doc__,
            aliases=aliases,
            **kwargs
        )
        self._add_dry_run(parser)
        parser.set_defaults(symph_func=method_func)
        return parser

    # ==================== Action API ====================
    def _setup_delete(self):
        parser = self._add_subparser('delete', aliases=['d'])
        self._add_experiment_name(parser, required=False, positional=True)
        parser.add_argument(
            '-f', '--force',
            action='store_true',
            help='force delete, do not show confirmation message.'
        )

    def _setup_delete_batch(self):
        parser = self._add_subparser('delete-batch', aliases=['db'])
        parser.add_argument('experiment_name', type=str)
        parser.add_argument(
            '-f', '--force',
            action='store_true',
            help='force delete, do not show confirmation message.'
        )

    def _setup_scp(self):
        parser = self._add_subparser('scp', aliases=['cp'])
        parser.add_argument(
            'src_file',
            help='source file or folder. "[[<process_group>/]<process>]:/file/path" denotes remote.'
        )
        parser.add_argument(
            'dest_file',
            help='destination file or folder. "[[<process_group>/]<process>]:/file/path" denotes remote.'
        )
        self._add_experiment_name(parser, required=False, positional=True)

    def _setup_ssh(self):
        parser = self._add_subparser('ssh', aliases=[])
        self._add_component_arg(parser)
        self._add_experiment_name(parser, required=False, positional=True)
    
    def _setup_exec(self):
        """
        Actual exec commands must be added after "--"
        will throw error if no "--" in command args
        """
        parser = self._add_subparser('exec', aliases=['x'])
        self._add_component_arg(parser)
        self._add_experiment_name(parser, required=False, positional=True)

    # ==================== Query API ====================
    def _setup_log(self):
        parser = self._add_subparser('log', aliases=['logs', 'l'])
        self._add_component_arg(parser)
        self._add_experiment_name(parser, required=False, positional=True)
        parser.add_argument(
            '-f', '--follow',
            action='store_true',
            help='if the logs should be streamed.'
        )
        parser.add_argument(
            '-s', '--since',
            default='0',
            help='only show logs newer than a relative duration like 5s, 2m, 3h.'
        )
        parser.add_argument(
            '-t', '--tail',
            type=int,
            default=100,
            help='Only show the most recent lines of log. -1 to show all log lines.'
        )

    def _setup_list_experiments(self):
        parser = self._add_subparser(
            'list-experiments',
            aliases=['ls', 'exps', 'experiments']
        )
        # no arg to get the current namespace
        self._add_experiment_name(parser, required=False, positional=True)
    
    def _setup_experiment(self):
        parser = self._add_subparser(
            'experiment',
            aliases=['exp']
        )
        # no arg to get the current namespace
        self._add_experiment_name(parser, required=False, positional=True)
    
    def _setup_process(self):
        """
            same as 'symphony list pod'
        """
        parser = self._add_subparser('process', aliases=['p', 'processes'])
        self._add_experiment_name(parser, required=False, positional=True)

    def _setup_visit(self):
        parser = self._add_subparser('visit', aliases=['vi'])
        parser.add_argument('service_name', help='the name of the service to visit')
        parser.add_argument(
            '-u', '--url-only',
            action='store_true',
            help='only show the URL without opening the browser.'
        )
        self._add_experiment_name(parser, required=False, positional=True)

    # ==================== helpers ====================
    def _add_dry_run(self, parser):
        parser.add_argument(
            '-dr', '--dry-run',
            action='store_true',
            help='print the kubectl command without actually executing it.'
        )

    def _add_experiment_name(self, parser, required=True, positional=True):
        help_str = "experiment name will be used as namespace for DNS. " \
                   "Should only contain lower case letters, digits, and hypen. " \
                   "'_' ' ' '.' are not allowed and will be converted to hyphen."
        if positional and required:
            parser.add_argument(
                'experiment_name',
                type=sanitize_experiment_name,
                nargs=None,
                help=help_str
            )
        elif positional and not required:
            parser.add_argument(
                'experiment_name',
                type=sanitize_experiment_name,
                nargs='?',
                default=None,
                help=help_str
            )
        else:
            parser.add_argument(
                '-e', '--exp', '--experiment', '--experiment-name',
                dest='experiment_name',
                type=sanitize_experiment_name,
                default=None,
                help=help_str,
            )

    def _add_component_arg(self, parser):
        parser.add_argument(
            'component_name',
            help="[<process_group>/]<process>"
        )

    # ===============================================================
    # ==================== Commandline functions ====================
    # ===============================================================
    def _interactive_find_exp(self, name, max_matches=10):
        """
        Find partial match of namespace, ask user to verify before switching to
        ns or delete experiment.
        Used in:
        - symphony delete
        - symphony ns
        Disabled when --force
        """
        matches = self.cluster.fuzzy_match_experiment(name)
        if isinstance(matches, str):
            return matches  # exact match
        if len(matches) == 0:
            print_err('[Error] Experiment `{}` not found. '
                      'Please run `symphony list ns` and check for typos.'.format(name))
            return None
        elif len(matches) == 1:
            match = matches[0]
            print_err('[Warning] No exact match. Fuzzy match only finds one candidate: "{}"'
                      .format(match))
            return match
        prompt = '\n'.join(['{}) {}'.format(i, n) for i, n in enumerate(matches)])
        prompt = ('Cannot find exact match. Fuzzy matching: \n'
                  '{}\nEnter your selection 0-{} (enter to select 0, q to quit): '
                  .format(prompt, len(matches) - 1))
        ans = input(prompt)
        if not ans.strip():  # blank
            ans = '0'
        try:
            ans = int(ans)
        except ValueError:  # cannot convert to int, quit
            print_err('aborted')
            return None
        if ans >= len(matches):
            raise IndexError('[Error] Must enter a number between 0 - {}'.format(len(matches)-1))
        return matches[ans]

    def _symphony_delete(self, experiment_name, force, dry_run):
        """
        Stop an experiment, delete corresponding pods, services, and namespace.
        If experiment_name is omitted, default to deleting the current namespace.
        """
        cluster = self.cluster
        if experiment_name:
            to_delete = experiment_name
            if force:
                assert to_delete in cluster.list_experiments(), \
                    '[Error] Experiment `{}` not found. ' \
                    'Run without --force to fuzzy match the name.'.format(to_delete)
            else:  # fuzzy match namespace to delete
                to_delete = self._interactive_find_exp(to_delete)
                if to_delete is None:
                    return
        else:
            to_delete = cluster.current_experiment()

        if not force and not dry_run:
            ans = input('Confirm delete {}? <enter>=yes,<n>=no: '.format(to_delete))
            if ans not in ['', 'y', 'yes', 'Y']:
                print('aborted')
                return

        cluster.delete(experiment_name=to_delete)
        print('deleting all resources under experiment "{}"'.format(to_delete))

    def symphony_delete(self, args):
        """
        Stop an experiment, delete corresponding pods, services, and namespace.
        If experiment_name is omitted, default to deleting the current namespace.
        """
        self._symphony_delete(args.experiment_name, args.force, args.dry_run)

    def symphony_delete_batch(self, args):
        """
        Stop an experiment, delete corresponding pods, services, and namespace.
        If experiment_name is omitted, default to deleting the current namespace.
        Matches all possible experiments
        """
        experiments = self.cluster.list_experiments()
        for experiment in experiments:
            if re.match(args.experiment_name, experiment):
                self._symphony_delete(experiment, args.force, args.dry_run)

    def symphony_list_experiments(self, args):
        """
        `symphony ls`: list all experiments
        aliases `symphony exps`, `symphony experiments`
        """
        for exp in self.cluster.list_experiments():
            print(exp)

    def symphony_experiment(self, args):
        """
        `symphony exp`: show the current experiment
        `symphony exp <namespace>`: switch context to another experiment
        """
        cluster = self.cluster
        name = args.experiment_name
        if name:
            name = self._interactive_find_exp(name)
            if name is None:
                return
            cluster.set_experiment(name)
        else:
            print(cluster.current_experiment())

    def _get_experiment(self, args):
        """
            Returns: <fuzzy-matched-name>
        """
        name = args.experiment_name
        if not name:
            return None
        name = self._interactive_find_exp(name)
        if not name:
            sys.exit(1)
        return name

    def symphony_process(self, args):
        """
            same as 'symphony list pod'
        """
        name = self._get_experiment(args)
        status_headers = self.cluster.status_headers()
        data = self.cluster.describe_experiment(name)
        output = self._print_experiment(status_headers, data)
        print(output)
        
    def _print_experiment(self, status_headers, data, min_width=5, max_width=1000, pad=2):
        headers = ['Group', 'Name'] + status_headers
        columns = {x: [] for x in headers}
        for pg_name, process_group in data.items():
            for p_name, status in process_group.items():
                if pg_name is None:
                    pg_name = ''
                columns['Group'].append(pg_name)
                columns['Name'].append(p_name)
                for header in status_headers:
                    columns[header].append(str(status[header]))
        width = {}
        for key in columns:
            w = max([len(x) for x in columns[key]] + [len(key)]) + 2
            w = max(w, min_width)
            w = min(w, max_width)
            width[key] = w
        row_format = ''.join(['{{:<{}}}'.format(width[header]) for header in headers])
        rows = [row_format.format(*headers)]
        for i in range(len(columns['Name'])):
            row_data = [columns[x][i] for x in headers]
            rows.append(row_format.format(*row_data))
        return '\n'.join(rows)

    def symphony_log(self, args):
        """
        Show logs of components:
        """
        experiment_name = self._get_experiment(args)
        process_group_name, process_name = self._separate_component_path(args.component_name, experiment_name)
        self.cluster.get_log(
            experiment_name=experiment_name,
            process_name=process_name,
            process_group=process_group_name,
            follow=args.follow,
            since=args.since,
            tail=args.tail,
            print_logs=True
        )

    def symphony_exec(self, args):
        """
        Exec command on a component:
        kubectl exec -ti <component> -- <command>
        """
        experiment_name = self._get_experiment(args)
        process_group_name, process_name = self._separate_component_path(args.component_name, experiment_name)
        if not args.has_remainder:
            raise RuntimeError(
                'please enter your command after "--". '
                'One and only one "--" must be present. \n'
                'Example: symphony exec learner [optional-experiment_name] -- ls -alf /fs/'
            )
        commands = args.remainder
        self.cluster.exec_command(
            process_name=args.component_name,
            process_group_name=process_group_name,
            command=commands,
            experiment_name=self._get_experiment(args)
        )

    def symphony_scp(self, args):
        """
        https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#cp
        symphony cp /my/local/file learner:/remote/file mynamespace
        is the same as
        kubectl cp /my/local/file mynamespace/nonagent:/remote/file -c learner
        """
        exp = self._get_experiment(args)
        src_p, src_pg, src_path = self._format_scp_path(args.src_file, exp)
        dest_p, dest_pg, dest_path = self._format_scp_path(args.dest_file, exp)
        assert (src_p is None) != (dest_p is None), \
            '[Error] one of "src_file" and "dest_file" must be remote and the other local.'
        self.cluster.transfer_file(exp, src_path, dest_path, src_process=src_p, 
                                    src_process_group=src_pg, 
                                    dest_process=dest_p, 
                                    dest_process_group=dest_pg)

    def symphony_ssh(self, args):
        """
        Interactive /bin/bash into the pod
        kubectl exec -ti <component> -- /bin/bash
        """
        exp = self._get_experiment(args)
        pg, p = self._separate_component_path(args.component_name, exp)
        self.cluster.login(experiment_name=exp, process_name=p, process_group_name=pg)

    def symphony_visit(self, args):
        url = self.cluster.external_url(self._get_experiment(args), args.service_name)
        if url:
            url = 'http://' + url
            print(url)
            if not args.url_only:
                webbrowser.open(url)
        else:
            print_err('Tensorboard does not yet have an external IP.')

    # =============================================================
    # ==================== Commandline helpers ====================
    # =============================================================
    def _separate_component_path(self, path, experiment_name):
        """
        Args:
            path(string): 'process_group/process' or 'process'
        Returns
            process_group_name (None if not present), process_name
        """

        if path.find('/') >= 0:
            assert len(path.split('/')) == 2, 'Invalid component path {}'.format(path)
            process_group, process = path.split('/')
            pgs = self.cluster.find_process(experiment_name, process)
            if process_group in pgs:
                return process_group, process
            else:
                raise ValueError('Cannot find {}'.format(path))
        else:
            pgs = self.cluster.find_process(experiment_name, path)
            if len(pgs) == 0:
                raise ValueError('Cannot find process {}'.format(path))
            elif len(pgs) == 1:
                return pgs[0], path
            else:
                raise ValueError('Multiple process groups contain {}: {}, which do you mean?'.format(pgs, path))

    def _format_scp_path(self, f, experiment_name):
        """
        Returns process_group, process, path for a path provided to scp
        """
        if ':' in f:
            path_name, path = f.split(':')
            pg, p = self._separate_component_path(path_name, experiment_name)
            return pg, p, path
        else:
            return None, None, f

def create_symphony_parser():
    """
    Creates a master parser with sub_parsers
    Returns:
        master_parser(argparse.ArgumentParser())
        subparsers(master_parser.add_subparsers(help='action commands',dest='action'))
        claimed_commands(set(string)): commands used by symphony
    """
    master_parser = argparse.ArgumentParser()

    subparsers = master_parser.add_subparsers(
        help='action commands',
        dest='action'  # will store to parser.subcommand_name
    )
    symph_cmd = SymphonyCommandLine(subparsers)
    return master_parser, subparsers, symph_cmd.claimed_commands

def add_symphony_parser(subparsers):
    """
    Takes add symphony command to subparsers
    Args:
        subparsers: subparsers that symphony adds commands to
    Returns:
        claimed_commands(set(string)): commands used by symphony
    """
    symph_cmd = SymphonyCommandLine(subparsers)
    return symph_cmd.claimed_commands

def symph_parse_args(parser, argv=None):
    """
    Truncates argv by removing everything after '--'.
    Args:
        argv(list(str))
    """
    if argv is None:
        argv = sys.argv[1:]
    assert argv.count('--') <= 1, \
        'command line can only have at most one "--"'
    if '--' in argv:
        idx = argv.index('--')
        remainder = argv[idx+1:]
        argv = argv[:idx]
        has_remainder = True  # even if remainder itself is empty
    else:
        remainder = []
        has_remainder = False

    args = parser.parse_args(argv)
    args.remainder = remainder
    args.has_remainder = has_remainder

    return args, argv

def symph_exec_args(args):
    """
    If the command is symphony related, execute the command and return True
    Otherwise, return False
    This is done by reading symph_func field of the namespace
    """
    if 'symph_func' in args:
        args.symph_func(args)
        return True
    return False
    return argv, has_remainder, remainder
