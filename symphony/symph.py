# Commandline interface of symphony, allows easy experiment management
# 
# TODO: git snapshot
# TODO: global config (of symphony), so we can configure stuff
from symphony.utils.common import sanitize_name
from symphony.cluster.kubecluster import KubeCluster
import symphony.utils.commandline as cmdline
from symphony.utils.common import print_err
import argparse
import sys
import re


def sanitize_experiment_name(name):
    """
        Allows None through so that kubecluster will use default name instead
    """
    if name is None:
        return name
    else:
        return sanitize_name(name)


class SymphonyParser:
    def __init__(self):
        self._master_parser = argparse.ArgumentParser()
        self._add_dry_run(self._master_parser)

        self._subparsers = self._master_parser.add_subparsers(
            help='symphony action commands',
            dest='symphony_action'  # will store to parser.subcommand_name
        )
        self._subparsers.required = True

    def setup_master(self):
        """
        Main function that returns the configured parser
        """
        self._setup_delete()
        self._setup_delete_batch()
        self._setup_log()
        self._setup_experiment()
        # TODO: experiments
        self._setup_process()
        
        self._setup_exec() # TODO
        self._setup_scp() # TODO
        self._setup_ssh() # TODO

        self._setup_ssh_node() # TODO: lower priority
        # TODO: read external service

        ### One needs to draw a line in the sand here 
        ### Above are instructions that can be universal to all cluster interfaces
        ### That users with limited knowledge of kubernetes can use
        ###
        ### Below are: Advanced options
        ### That have to leak kubernetes related information 
        ### and requires users to have kubernetes related knowledge
        self._setup_list()
        self._setup_describe()

        # These are surreal-specific functionalities. I might have a way 
        # of aggregating them
        # self._setup_create()
        # self._setup_create_dev()
        # self._setup_restore()
        # self._setup_resume() # TODO: what about restore and resume

        # self._setup_tensorboard()
        # self._setup_create_tensorboard()

        # self._setup_download_experiment() # TODO: what to do with this

        # self._setup_ssh_nfs() # 
        # self._setup_configure_ssh()
        # self._setup_capture_tensorboard()
        return self._master_parser

    def _add_subparser(self, name, aliases, **kwargs):
        method_name = 'symphony_' + name.replace('-', '_')
        raw_method = getattr(Symphony, method_name)  # Symphony.symphony_create()

        def _symphony_func(args):
            """
            Get function that processes parsed args and runs symphony actions
            """
            symphony_object = Symphony(args)
            raw_method(symphony_object, args)

        parser = self._subparsers.add_parser(
            name,
            help=raw_method.__doc__,
            aliases=aliases,
            **kwargs
        )
        self._add_dry_run(parser)
        parser.set_defaults(func=_symphony_func)
        return parser

    # def _setup_create(self): Delegate to project

    # def _setup_create_dev(self): Delegate to individual project

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

    # def _setup_restore(self):
    #     parser = self._add_subparser('restore', aliases=[])
    #     parser.add_argument(
    #         '-new', '--new',
    #         dest='experiment_name',
    #         type=self._process_experiment_name,
    #         required=True,
    #         help='Start a new experiment from the old checkpoint. '
    #              'experiment name will be used as namespace for DNS. '
    #              'Should only contain lower case letters, digits, and hypen. '
    #              'Underscores and dots are not allowed and will be converted to hyphen.'
    #     )
    #     parser.add_argument(
    #         '-old', '--old',
    #         dest='restore_experiment',
    #         required=True,
    #         help="old experiment name to restore from. "
    #              "you can also give full path to the folder on the shared FS: "
    #              "'/fs/experiments/myfriend/.../'"
    #     )
    #     self._add_restore_args(parser)
    #     self._add_create_args(parser)

    # def _setup_resume(self):
    #     parser = self._add_subparser('resume', aliases=['continue'])
    #     self._add_experiment_name(parser)
    #     self._add_restore_args(parser)
    #     self._add_create_args(parser)  # --force is automatically turned on

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

    def _setup_experiment(self):
        parser = self._add_subparser(
            'experiment',
            aliases=['exp']
        )
        # no arg to get the current namespace
        self._add_experiment_name(parser, required=True, positional=True)

    def _setup_list(self):
        parser = self._add_subparser('list', aliases=['ls'])
        parser.add_argument(
            'resource',
            choices=['ns', 'namespace', 'namespaces',
                     'e', 'exp', 'experiment', 'experiments',
                     'p', 'pod', 'pods',
                     'no', 'node', 'nodes',
                     's', 'svc', 'service', 'services'],
            default='ns',
            nargs='?',
            help='list experiment, pod, and node'
        )
        self._add_experiment_name(parser, required=False, positional=True)
        parser.add_argument(
            '-a', '--all',
            action='store_true',
            help='show all resources from all namespace.'
        )

    def _setup_process(self): # TODO: namespace
        """
            same as 'symphony list pod'
        """
        parser = self._add_subparser('process', aliases=['p', 'processes'])
        self._add_experiment_name(parser, required=False, positional=True)
        parser.add_argument(
            '-a', '--all',
            action='store_true',
            help='show all pods from all namespace.'
        )

    # def _setup_tensorboard(self): TODO: external service
    #     parser = self._add_subparser('tensorboard', aliases=['tb'])
    #     self._add_experiment_name(parser, required=False, positional=True)
    #     parser.add_argument(
    #         '-u', '--url-only',
    #         action='store_true',
    #         help='only show the URL without opening the browser.'
    #     )

    # def _setup_create_tensorboard(self):
    #     parser = self._add_subparser('create-tensorboard', aliases=['ctb'])
    #     parser.add_argument(
    #         'remote_experiment_subfolder',
    #         help='remote subfolder under <fs_mount_path>/<root_subfolder>.'
    #     )
    #     parser.add_argument(
    #         '-a', '--absolute-path',
    #         action='store_true',
    #         help='use absolute remote path instead of '
    #              '<fs_mount_path>/<root_subfolder>/<remote_folder>'
    #     )
    #     parser.add_argument(
    #         '-p', '--pod-type',
    #         default='tensorboard',
    #         help='pod type for the tensorboard pod (specified in ~/.surreal.yml). '
    #              'please use the smallest compute instance possible.'
    #     )

    def _setup_describe(self): # TODO: We can probably expose pod here
        parser = self._add_subparser('describe', aliases=['des'])
        parser.add_argument(
            'pod_name',
            help="should be either 'agent-<N>' or 'nonagent'"
        )
        self._add_experiment_name(parser, required=False, positional=True)

    def _setup_exec(self):
        """
        Actual exec commands must be added after "--"
        will throw error if no "--" in command args
        """
        parser = self._add_subparser('exec', aliases=['x'])
        self._add_component_arg(parser)
        self._add_experiment_name(parser, required=False, positional=True)

    def _setup_scp(self):
        parser = self._add_subparser('scp', aliases=['cp'])
        parser.add_argument(
            'src_file',
            help='source file or folder. "<component>:/file/path" denotes remote.'
        )
        parser.add_argument(
            'dest_file',
            help='destination file or folder. "<component>:/file/path" denotes remote.'
        )
        self._add_experiment_name(parser, required=False, positional=True)

    # def _setup_download_experiment(self):
    #     parser = self._add_subparser('download-experiment',
    #                                  aliases=['de', 'download'])
    #     parser.add_argument(
    #         'remote_experiment_subfolder',
    #         help='remote subfolder under <fs_mount_path>/<root_subfolder>.'
    #     )
    #     parser.add_argument(
    #         '-a', '--absolute-path',
    #         action='store_true',
    #         help='use absolute remote path instead of '
    #              '<fs_mount_path>/<root_subfolder>/<remote_folder>'
    #     )
    #     parser.add_argument(
    #         '-o', '--output-path',
    #         default='.',
    #         help='local folder path to download to'
    #     )
    #     parser.add_argument(
    #         '-m', '--match-fuzzy',
    #         action='store_true',
    #         help='enable fuzzy matching with the currently running namespaces'
    #     )

    def _setup_ssh(self):
        parser = self._add_subparser('ssh', aliases=[])
        self._add_component_arg(parser)
        self._add_experiment_name(parser, required=False, positional=True)

    def _setup_ssh_node(self):
        parser = self._add_subparser('ssh-node', aliases=['sshnode'])
        parser.add_argument('node_name', help='gcloud only')

    # def _setup_ssh_nfs(self):
    #     parser = self._add_subparser('ssh-nfs', aliases=['sshnfs'])

    # def _setup_configure_ssh(self):
    #     parser = self._add_subparser('configure-ssh', aliases=['configssh'])

    # def _setup_label(self):
    #     """
    #     Shouldn't manually label if you are using kube autoscaling
    #     """
    #     parser = self._add_subparser('label', aliases=[])
    #     parser.add_argument(
    #         'old_labels',
    #         help='select nodes according to their old labels'
    #     )
    #     parser.add_argument(
    #         'new_labels',
    #         type=_process_labels,
    #         help='mark the selected nodes with new labels in format '
    #              '"mylabel1=myvalue1,mylabel2=myvalue2"'
    #     )

    # def _setup_capture_tensorboard(self):
    #     parser = self._add_subparser('capture-tensorboard', aliases=['cptb'])
    #     parser.add_argument(
    #         'experiment_prefix',
    #         help='capture tensorboard screenshot for all prefix matched experiments,\
    #               one can also use regex'  
    #     )

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
            help="the name of a process of the experiment"
        )

    # def _add_create_args(self, parser):
    #     """
    #     Used in create(), restore(), resume()
    #     """
    #     parser.add_argument(
    #         '-at', '--agent-pod-type',
    #         default='agent',
    #         help='key in ~/.surreal.yml `pod_types` section that describes spec for agent pod. '
    #              'Default: "agent"'
    #     )
    #     parser.add_argument(
    #         '-nt', '--nonagent-pod-type',
    #         default='nonagent-cpu',
    #         help='key in ~/.surreal.yml `pod_types` section that describes spec for '
    #              'nonagent pod with multiple containers: learner, ps, tensorboard, etc. '
    #              'Default: "nonagent-cpu"'
    #     )
    #     parser.add_argument(
    #         '-nos', '--no-snapshot',
    #         action='store_true',
    #         help='Unless this flag is on, Surreal will take snapshot of the specified '
    #              'git repos in ~/.surreal.yml and upload to your remote Github branch.'
    #     )
    #     parser.add_argument(
    #         '-f', '--force',
    #         action='store_true',
    #         help='force overwrite an existing symphony.yml file '
    #              'if its experiment folder already exists.'
    #     )

    # def _add_restore_args(self, parser):
    #     """
    #     Used in restore(), resume()
    #     If remainders (cmd line args after "--") are specified,
    #     override the saved launch cmd args
    #     """
    #     parser.add_argument(
    #         '--config-py',
    #         default=None,
    #         help='If unspecified, defaults to the saved launch command. '
    #              'location of python script **in the Kube pod** that contains the '
    #              'runnable config. If the path does not start with /, defaults to '
    #              'home dir, i.e. /root/ on the pod'
    #     )
    #     parser.add_argument(
    #         '-n', '--num-agents',
    #         type=int,
    #         default=None,
    #         help='If unspecified, defaults to the saved launch command. '
    #              'number of agents to run in parallel.'
    #     )
        # the following should not be managed by Symphony, should be set in config.py
        # session_config.checkpoint.learner.restore_target
        # parser.add_argument(
        #     '--best',
        #     action='store_true',
        #     help='restore from the best checkpoint, otherwise from history'
        # )
        # parser.add_argument(
        #     '-t', '--target',
        #     default='0',
        #     help='see "Checkpoint" class. Restore target can be one of '
        #          'the following semantics:\n'
        #          '- int: 0 for the last (or best), 1 for the second last (or best), etc.'
        #          '- global steps of the ckpt file, the suffix string right before ".ckpt"'
        # )


class Symphony:
    def __init__(self, args):
        self.kube = KubeCluster(dry_run=args.dry_run)

    def _interactive_find_exp(self, name, max_matches=10):
        """
        Find partial match of namespace, ask user to verify before switching to
        ns or delete experiment.
        Used in:
        - symphony delete
        - symphony ns
        Disabled when --force
        """
        matches = self.kube.fuzzy_match_experiment(name, max_matches=max_matches)
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
        kube = self.kube
        if experiment_name:
            to_delete = experiment_name
            if force:
                assert to_delete in kube.list_experiments(), \
                    '[Error] Experiment `{}` not found. ' \
                    'Run without --force to fuzzy match the name.'.format(to_delete)
            else:  # fuzzy match namespace to delete
                to_delete = self._interactive_find_exp(to_delete)
                if to_delete is None:
                    return
        else:
            to_delete = kube.current_experiment()

        assert to_delete not in ['default', 'kube-public', 'kube-system'], \
            'cannot delete reserved names: default, kube-public, kube-system'
        if not force and not dry_run:
            ans = input('Confirm delete {}? <enter>=yes,<n>=no: '.format(to_delete))
            if ans not in ['', 'y', 'yes', 'Y']:
                print('aborted')
                return

        kube.delete(experiment_name=to_delete)
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
        experiments = self.kube.list_experiments()
        for experiment in experiments:
            if re.match(args.experiment_name, experiment):
                self._symphony_delete(experiment, args.force, args.dry_run)

    def symphony_experiment(self, args):
        """
        `symphony ns`: show the current namespace/experiment
        `symphony ns <namespace>`: switch context to another namespace/experiment
        """
        kube = self.kube
        name = args.experiment_name
        print(args)
        if name:
            name = self._interactive_find_exp(name)
            if name is None:
                return
            kube.set_namespace(name)
        else:
            print(kube.current_experiment())

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

    def symphony_list(self, args):
        """
            List resource information: namespace, pods, nodes, services
        """
        run = lambda cmd: \
            cmdline.run_verbose(cmd, print_out=True, raise_on_error=False)
        if args.all:
            ns_cmd = ' --all-namespaces'
        elif args.experiment_name:
            ns_cmd = ' --namespace ' + self._get_experiment(args)
        else:
            ns_cmd = ''
        if args.resource in ['ns', 'namespace', 'namespaces',
                             'e', 'exp', 'experiment', 'experiments']:
            run('kubectl get namespace')
        elif args.resource in ['p', 'pod', 'pods']:
            run('kubectl get pods -o wide' + ns_cmd)
        elif args.resource in ['no', 'node', 'nodes']:
            run('kubectl get nodes -o wide' + ns_cmd)
        elif args.resource in ['s', 'svc', 'service', 'services']:
            run('kubectl get services -o wide' + ns_cmd)
        else:
            raise ValueError('INTERNAL ERROR: invalid symphony list choice.')

    def symphony_process(self, args):
        """
            same as 'symphony list pod'
        """
        args.resource = 'pod'
        self.symphony_list(args)

    def symphony_describe(self, args):
        """
        Same as `kubectl describe pod <pod_name>`
        """
        self.kube.describe(args.pod_name, experiment_name=self._get_experiment(args))


    def symphony_log(self, args):
        """
        Show logs of Surreal components: agent-<N>, learner, ps, etc.
        https://kubernetes-v1-4.github.io/docs/user-guide/kubectl/kubectl_logs/
        """

        self.kube.logs_print(
            process_name=args.component_name,
            follow=args.follow,
            since=args.since,
            tail=args.tail,
            experiment_name=self._get_experiment(args)
        )

    def symphony_exec(self, args):
        """
        Exec command on a Surreal component: agent-<N>, learner, ps, etc.
        kubectl exec -ti <component> -- <command>
        """
        # TODO: fix this
        if not args.has_remainder:
            raise RuntimeError(
                'please enter your command after "--". '
                'One and only one "--" must be present. \n'
                'Example: symphony exec learner [optional-namespace] -- ls -alf /fs/'
            )
        commands = args.remainder
        if len(commands) == 1:
            commands = commands[0]  # don't quote the singleton string
        # self.kube.exec(
        #     process_name=args.component_name,
        #     commands,
        #     namespace=self._get_experiment(args)
        # )

    def symphony_scp(self, args):
        """
        https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#cp
        symphony cp /my/local/file learner:/remote/file mynamespace
        is the same as
        kubectl cp /my/local/file mynamespace/nonagent:/remote/file -c learner
        """
        # TODO: fix this
        self.kube.scp_surreal(
            args.src_file, args.dest_file, self._get_experiment(args)
        )

    # def symphony_download_experiment(self, args):
    #     """
    #     Same as `symphony scp learner:<mount_path>/<root_subfolder>/experiment-folder .`
    #     """
    #     kube = self.kube
    #     remote_subfolder = args.remote_experiment_subfolder
    #     if not args.absolute_path:
    #         if args.match_fuzzy:
    #             assert '/' not in remote_subfolder, \
    #                 "fuzzy match does not allow '/' in experiment name"
    #             remote_subfolder = self._interactive_find_exp(remote_subfolder)
    #             remote_subfolder = kube.strip_username(remote_subfolder)
    #         remote_path = kube.get_remote_experiment_folder(remote_subfolder)
    #     else:
    #         assert not args.match_fuzzy, \
    #             'cannot fuzzy match when --absolute-path is turned on.'
    #         remote_path = remote_subfolder
    #     # the experiment folder will be unpacked if directly scp to "."
    #     output_path = U.f_join(args.output_path, U.f_last_part_in_path(remote_path))
    #     kube.scp_surreal(
    #         'learner:' + remote_path, output_path
    #     )

    def symphony_ssh(self, args):
        """
        Interactive /bin/bash into the pod
        kubectl exec -ti <component> -- /bin/bash
        """
        # TODO: fix
        self.kube.exec_surreal(
            args.component_name,
            '/bin/bash',
            namespace=self._get_experiment(args)
        )

    def symphony_ssh_node(self, args):
        """
        GCloud only, ssh into gcloud nodes.
        Run `symphony list node` to get the node name.
        Run with --configure-ssh if ssh config is outdated
        """
        errcode = self.kube.gcloud_ssh_node(args.node_name)
        if errcode != 0:
            print_err('GCloud ssh aliases might be outdated. Try:\n'
                      'symphony configure-ssh && '
                      'symphony ssh-node ' + args.node_name)

    # def symphony_ssh_nfs(self, args):
    #     """
    #     GCloud only, ssh into gcloud NFS.
    #     Its server address should be specified in ~/.surreal.yml
    #     Run with --configure-ssh if ssh config is outdated
    #     """
    #     errcode = self.kube.gcloud_ssh_fs()
    #     if errcode != 0:
    #         print_err('GCloud ssh aliases might be outdated. Try:\n'
    #                   'symphony configure-ssh && symphony ssh-nfs')

    def symphony_configure_ssh(self, args): # TODO: shall we keep this?
        errcode = self.kube.gcloud_configure_ssh()
        if errcode == 0:
            print('GCloud ssh configured successfully')

    # def symphony_tensorboard(self, args):
    #     """
    #     Open tensorboard in your default browser.
    #     """
    #     url = self.kube.external_ip(
    #         'tensorboard',
    #         namespace=self._get_experiment(args)
    #     )
    #     if url:
    #         url = 'http://' + url
    #         print(url)
    #         if not args.url_only:
    #             webbrowser.open(url)
    #     else:
    #         print_err('Tensorboard does not yet have an external IP.')

    # def symphony_create_tensorboard(self, args):
    #     """
    #     Create a single pod that displays tensorboard of an old experiment.
    #     After the service is up and running, run `symphony tb` to open the external
    #     URL in your browser
    #     """
    #     kube = self.kube
    #     remote_subfolder = args.remote_experiment_subfolder
    #     rendered_name = (remote_subfolder.replace('/', '-')
    #                      .replace('.', '-').replace('_', '-'))
    #     rendered_path = kube.get_path('symphony-tensorboard', rendered_name + '.yml')
    #     U.f_mkdir_in_path(rendered_path)
    #     if not args.absolute_path:
    #         remote_path = kube.get_remote_experiment_folder(remote_subfolder)
    #     else:
    #         remote_path = remote_subfolder
    #     namespace = kube.create_tensorboard(
    #         remote_path=remote_path,
    #         jinja_template=self._find_symphony_template('tensorboard_template.yml'),
    #         rendered_path=rendered_path,
    #         tensorboard_pod_type=args.pod_type
    #     )
    #     print('Creating standalone tensorboard pod. ')
    #     print('Please run `symphony tb` to open the tensorboard URL in your browser '
    #           'when the service is up and running. '
    #           'You can check service by `symphony list service`')
    #     print('  remote_path:', remote_path)
    #     print('  tensorboard_pod_type:', args.pod_type)
    #     # switch to the standalone pod namespace just created
    #     kube.set_namespace(namespace)

    # def symphony_capture_tensorboard(self, args):
    #     print('############### \n '
    #         'If this command fails, check that your surreal.yml contains\n'
    #         'capture_tensorboard:'
    #         '  node_path: ...'
    #         '  library_path: ...'
    #         '###############')
    #     pattern = args.experiment_prefix
    #     out, _, _ = self.kube.run_verbose('get namespace -o name',
    #                             print_out=False,raise_on_error=True)
    #     # out is in format namespaces/[namespace_name]
    #     namespaces = [x.strip()[len('namespaces/'):] for x in out.split()]
    #     cwd = os.getcwd()
    #     processes = []
    #     for namespace in namespaces:
    #         if re.match(pattern, namespace):
    #             job = self.kube.capture_tensorboard(namespace)
    #             processes.append(job)
    #             # My computer cannot do everything at the same time unfortunately
    #             job.wait()
    #     # for process in processes:
    #     #     process.wait()

    # def symphony_label(self, args):
    #     """
    #     Label nodes in node pools
    #     """
    #     for label, value in args.new_labels:
    #         self.kube.label_nodes(args.old_labels, label, value)

    # def symphony_label_gcloud(self, args):
    #     """
    #     NOTE: you don't need this for autoscale

    #     Add default labels for GCloud cluster.
    #     Note that you have to create the node-pools with the exact names:
    #     "agent-pool" and "nonagent-pool-cpu"
    #     gcloud container node-pools create agent-pool-cpu -m n1-standard-2 --num-nodes=8

    #     Command to check whether the labeling is successful:
    #     kubectl get node -o jsonpath="{range .items[*]}{.metadata.labels['surreal-node']}{'\n---\n'}{end}"
    #     """
    #     kube = self.kube
    #     kube.label_nodes('cloud.google.com/gke-nodepool=agent-pool',
    #                      'surreal-node', 'agent-pool')
    #     kube.label_nodes('cloud.google.com/gke-nodepool=nonagent-pool',
    #                      'surreal-node', 'nonagent-pool')


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
