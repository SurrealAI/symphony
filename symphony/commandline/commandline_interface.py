import webbrowser
import argparse
import re
import sys
from symphony.utils.common import print_err


class SymphonyParser(object):
    def __init__(self):
        """
        This class adds parsers to sub_parser
        Args:
            sub_parser(generate by argparse.ArgumentParser().add_subparsers())
        """
        self.master_parser = argparse.ArgumentParser()

        self.subparsers = self.master_parser.add_subparsers(
            help='action commands',
            dest='action'  # will store to parser.subcommand_name
        )
        self.subparsers.required = True
        self._parsers_cache = {}

        self.cluster = self.create_cluster()

        self.setup()

    # ======================================================
    # ==================== Parser setup ====================
    # ======================================================
    def create_cluster(self):
        """
        creates the cluster to use for the experiment
        """
        raise NotImplementedError("Any subclass of SymphonyParser must implement create_cluster(self)")
        # config = SymphonyConfig()
        # cluster = Cluster.new(config.cluster_type, **config.cluster_args)
        # return cluster

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
        self._setup_switch_experiment() #
        self._setup_list_processes() #
        self._setup_log() #
        self._setup_visit() #

    def add_subparser(self, name, aliases, **kwargs):
        """ Add a subparser with name @name
        Args:
            name: The name of the sub parser. Method 'action_' + name will be called
                  For example, if name is 'log', `symphony log` will invoke self.action_log(args)
            aliases(list(str)): other names to invoke this command (e.g. ['l', 'logs'])
            kwargs: kwargs to provide to subparsers.add_parser()
        """
        method_name = 'action_' + name.replace('-', '_')
        if not hasattr(self, method_name):
            raise ValueError(
                'your parser class must define the method "{}()" '
                'in order to use the "{}" subparser'.format(method_name, name))
        method_func = getattr(self, method_name)  # Symphony.symphony_create()

        parser = self.subparsers.add_parser(
            name,
            help=method_func.__doc__,
            aliases=aliases,
            **kwargs
        )
        self._parsers_cache[name] = parser
        parser.set_defaults(func=method_func)
        return parser

    def get_subparser(self, name):
        return self._parsers_cache[name]

    # ==================== Action API ====================
    def _setup_delete(self):
        parser = self.add_subparser('delete', aliases=['d'])
        self._add_experiment_name(parser, required=False, positional=True)
        parser.add_argument(
            '-f', '--force',
            action='store_true',
            help='force delete, do not show confirmation message.'
        )
        self.add_dry_run(parser)

    def _setup_delete_batch(self):
        parser = self.add_subparser('delete-batch', aliases=['db'])
        parser.add_argument('experiment_names', nargs='+', type=str, metavar='experiment_name')
        parser.add_argument(
            '-f', '--force',
            action='store_true',
            help='force delete, do not show confirmation message.'
        )
        self.add_dry_run(parser)

    def _setup_scp(self):
        parser = self.add_subparser('scp', aliases=['cp'])
        parser.add_argument(
            'src_file',
            help='source file or folder. "[[<process_group>/]<process>]:/file/path" denotes remote.'
        )
        parser.add_argument(
            'dest_file',
            help='destination file or folder. "[[<process_group>/]<process>]:/file/path" denotes remote.'
        )
        self._add_experiment_name(parser, required=False, positional=True)
        self.add_dry_run(parser)

    def _setup_ssh(self):
        parser = self.add_subparser('ssh', aliases=[])
        self._add_component_arg(parser)
        self._add_experiment_name(parser, required=False, positional=True)

    def _setup_exec(self):
        """
        Actual exec commands must be added after "--"
        will throw error if no "--" in command args
        """
        parser = self.add_subparser('exec', aliases=['x'])
        self._add_component_arg(parser)
        self._add_experiment_name(parser, required=False, positional=True)

    # ==================== Query API ====================
    def _setup_log(self):
        parser = self.add_subparser('log', aliases=['logs', 'l'])
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
            default=500,
            help='Only show the most recent lines of log. -1 to show all log lines.'
        )

    def _setup_list_experiments(self):
        parser = self.add_subparser(
            'list-experiments',
            aliases=['ls', 'lse']
        )
        # no arg to get the current namespace
        self._add_experiment_name(parser, required=False, positional=True)

    def _setup_switch_experiment(self):
        parser = self.add_subparser(
            'switch-experiment',
            aliases=['e', 'se']
        )
        parser.add_argument(
            '-f', '--force',
            action='store_true',
            help='Switch to the experiment even if it does not exist on cluster'
        )
        # no arg to get the current namespace
        self._add_experiment_name(parser, required=False, positional=True)

    def _setup_list_processes(self):
        """
            same as 'symphony list pod'
        """
        parser = self.add_subparser(
            'list-processes',
            aliases=['lsp', 'p']
        )
        self._add_experiment_name(parser, required=False, positional=True)

    def _setup_visit(self):
        parser = self.add_subparser('visit', aliases=['vi'])
        parser.add_argument('service_name', help='the name of the service to visit')
        parser.add_argument(
            '-u', '--url-only',
            action='store_true',
            help='only show the URL without opening the browser.'
        )
        self._add_experiment_name(parser, required=False, positional=True)

    # ==================== helpers ====================
    def add_dry_run(self, parser):
        parser.add_argument(
            '-dr', '--dry-run',
            action='store_true',
            help='print the command without actually executing it.'
        )

    def _add_experiment_name(self, parser, required=True, positional=True):
        help_str = "experiment name will be used as namespace for DNS. " \
                   "Should only contain lower case letters, digits, and hypen. " \
                   "'_' ' ' '.' are not allowed and will be converted to hyphen."
        if positional and required:
            parser.add_argument(
                'experiment_name',
                nargs=None,
                help=help_str
            )
        elif positional and not required:
            parser.add_argument(
                'experiment_name',
                nargs='?',
                default=None,
                help=help_str
            )
        else:
            parser.add_argument(
                '-e', '--exp', '--experiment', '--experiment-name',
                dest='experiment_name',
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
    def _interactive_find_exp(self, name):
        matches, is_exact = self.cluster.fuzzy_match_experiment(name)
        assert isinstance(matches, list), 'INTERNAL'
        if is_exact:
            return matches[0]
        else:
            return self._interactive_find(matches, 'Experiment "{}"'.format(name))

    def _interactive_find_process(self, proc_path, exp_name):
        """
        Args:
            proc_path:
            - 'process_group/process': exact and must be matched verbatim
            - 'process': will be fuzzy matched to the closest process name in
                any process group. If two pgroups have the same process, will
                display a selection prompt.
        Returns
            process_group_name (None if not present), process_name
        """
        if '/' in proc_path:  # must be exact match
            assert len(proc_path.split('/')) == 2, \
                'Invalid process path {}. Should be "process_group/process"'.format(proc_path)
            pgroup, proc_name = proc_path.split('/')
            proc_pairs, is_exact = self.cluster.fuzzy_match_process(proc_name, exp_name)
            if is_exact:
                assert len(proc_pairs) == 1, \
                    'INTERNAL: (pgroup, pname) should be exactly one pair'
                return proc_pairs[0]
            else:
                raise ValueError('Cannot find process path "{}"'.format(proc_path))
        else:
            proc_pairs, is_exact = self.cluster.fuzzy_match_process(proc_path, exp_name)
            # avoid matching multiple PGroups with the same proc name
            # leave the above case to fuzzy matcher prompt
            if is_exact and len(proc_pairs) == 1:
                return proc_pairs[0]
            return self._interactive_find(proc_pairs,
                                          'Process "{}"'.format(proc_path))

    def _interactive_find(self, matches, error_message):
        """
        Find partial match of namespace, ask user to verify before switching to
        ns or delete experiment.
        Used in:
        - symphony delete
        - symphony ns
        Disabled when --force
        """
        if len(matches) == 0:
            print_err('[Error] {} not found. Please check for typos.'.format(error_message))
            sys.exit(1)
        elif len(matches) == 1:
            match = matches[0]
            print_err('[Warning] No exact match. Fuzzy match only finds one candidate: {}'
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
            sys.exit(1)
        if ans >= len(matches):
            print_err('[Error] Must enter a number between 0 - {}'.format(len(matches)-1))
            sys.exit(1)
        return matches[ans]

    def _delete(self, experiment_name, force, dry_run):
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

    def action_delete(self, args):
        """
        Stop an experiment, delete corresponding pods, services, and namespace.
        If experiment_name is omitted, default to deleting the current namespace.
        """
        self._delete(args.experiment_name, args.force, args.dry_run)

    def action_delete_batch(self, args):
        """
        Stop an experiment, delete corresponding pods, services, and namespace.
        If experiment_name is omitted, default to deleting the current namespace.
        Matches all possible experiments
        """
        for experiment_name in args.experiment_names:
            experiments = self.cluster.list_experiments()
            for experiment in experiments:
                if re.match(experiment_name, experiment):
                    self._delete(experiment, args.force, args.dry_run)

    def action_list_experiments(self, _):
        """
        `symphony ls`: list all experiments
        aliases `symphony exps`, `symphony experiments`
        """
        for exp in self.cluster.list_experiments():
            print(exp)

    def action_switch_experiment(self, args):
        """
        `symphony exp`: show the current experiment
        `symphony exp <namespace>`: switch context to another experiment
        """
        cluster = self.cluster
        name = args.experiment_name
        if name and args.force:
            cluster.set_experiment(name)
        elif name:
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

    def action_list_processes(self, args):
        """
            same as 'symphony list pod'
        """
        name = self._get_experiment(args)
        data = self.cluster.describe_experiment(name)
        output = self._print_experiment(data)
        print(output)

    def _print_experiment(self, data, min_width=5, max_width=1000, pad=2):
        if len(data) == 0:
            return ''
        headers = ['Group', 'Name']
        columns = {x:[] for x in headers}
        counter = 0
        for pg_name in data.keys():
            process_group = data[pg_name]
            for p_name in process_group.keys():
                status = process_group[p_name]
                if pg_name is None:
                    pg_name = ''
                columns['Group'].append(pg_name)
                columns['Name'].append(p_name)
                for header in status.keys():
                    if not header in headers:
                        headers.append(header)
                        columns[header] = []
                        for i in range(counter): # pad missing terms
                            columns[header].append('')
                    columns[header].append(str(status[header]))
                counter += 1
        width = {}
        for key in columns:
            w = max([len(x) for x in columns[key]] + [len(key)]) + pad
            w = max(w, min_width)
            w = min(w, max_width)
            width[key] = w
        row_format = ''.join(['{{:<{}}}'.format(width[header]) for header in headers])
        rows = [row_format.format(*headers)]
        for i in range(len(columns['Name'])):
            row_data = [columns[x][i] for x in headers]
            rows.append(row_format.format(*row_data))
        return '\n'.join(rows)

    def action_log(self, args):
        """
        Show logs of components:
        """
        experiment_name = self._get_experiment(args)
        process_group_name, process_name = \
            self._interactive_find_process(args.component_name, experiment_name)
        self.cluster.get_log(
            experiment_name=experiment_name,
            process_name=process_name,
            process_group=process_group_name,
            follow=args.follow,
            since=args.since,
            tail=args.tail,
            print_logs=True
        )

    def action_exec(self, args):
        """
        Exec command on a component:
        kubectl exec -ti <component> -- <command>
        """
        experiment_name = self._get_experiment(args)
        process_group_name, process_name = \
            self._interactive_find_process(args.component_name, experiment_name)
        if not args.has_remainder:
            raise RuntimeError(
                'please enter your command after "--". '
                'One and only one "--" must be present. \n'
                'Example: symphony exec learner [optional-experiment_name] -- ls -alf /fs/'
            )
        commands = args.remainder
        self.cluster.exec_command(
            process_name=process_name,
            process_group_name=process_group_name,
            command=commands,
            experiment_name=self._get_experiment(args)
        )

    def action_scp(self, args):
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

    def action_ssh(self, args):
        """
        Interactive /bin/bash into the pod
        kubectl exec -ti <component> -- /bin/bash
        """
        exp = self._get_experiment(args)
        pg, p = self._interactive_find_process(args.component_name, exp)
        self.cluster.login(experiment_name=exp, process_name=p, process_group_name=pg)

    def action_visit(self, args):
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
    def _format_scp_path(self, f, experiment_name):
        """
        Returns process_group, process, path for a path provided to scp
        """
        if ':' in f:
            path_name, path = f.split(':')
            pg, p = self._interactive_find_process(path_name, experiment_name)
            return pg, p, path
        else:
            return None, None, f

    # =============================================================
    # ========================= Main ==============================
    # =============================================================
    def main(self):
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

        args = self.master_parser.parse_args()
        args.remainder = remainder
        args.has_remainder = has_remainder

        args.func(args)
