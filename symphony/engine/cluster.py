"""
Cluster subclasses are the actual execution engines
"""
from collections import OrderedDict
from symphony.engine.application_config import SymphonyConfig


_BACKEND_REGISTRY = {}


class _BackendRegistry(type):
    def __new__(cls, name, bases, class_dict):
        cls = type.__new__(cls, name, bases, class_dict)
        cls_name = cls.__name__
        assert cls_name.endswith('Cluster'), \
            'cluster backend subclass names must end with "Cluster"'
        cls_name = cls_name[:-len('Cluster')].lower()
        _BACKEND_REGISTRY[cls_name] = cls
        return cls


class Cluster(metaclass=_BackendRegistry):
    def __init__(self, **kwargs):
        pass

    @classmethod
    def new(cls, backend, **kwargs):
        """
        To write generic cluster spec code, please use this factory method
        instead of subclass constructors

        Args:
            backend:
        """
        backend = backend.lower()
        assert backend in _BACKEND_REGISTRY, \
            '"{}" is not a valid cluster backend. Available backends: {}'.format(
                backend, list(_BACKEND_REGISTRY.keys())
            )
        cluster_cls = _BACKEND_REGISTRY[backend]
        assert issubclass(cluster_cls, Cluster), \
            'internal error: not subclass of Cluster'
        return cluster_cls(**kwargs)

    # ========================================================
    # ===================== Launch API =======================
    # ========================================================
    def new_experiment(self, *args, **kwargs):
        """
        Returns:
            new ExperimentSpec
        """
        raise NotImplementedError

    def launch(self, experiment_config, force=False, dry_run=False):
        """
        Launches an experiment specified by eperiment_config.
        Raises error if an experiment with the same name already exists
        Args:
            force: overwrites the experiment if it exists
            dry_run: only prints how processes are going to be run, do not actually run them
        """
        raise NotImplementedError

    def launch_batch(self, experiment_configs):
        for exp in experiment_configs:
            self.launch(exp)

    # ========================================================
    # ===================== Action API =======================
    # ========================================================
    def delete(self, experiment_name):
        """
        Deletes experiment with name @experiment_name. If the experiment doesn't
        exist, raise error
        """
        raise NotImplementedError

    def delete_batch(self, experiment_names):
        for exp in experiment_names:
            self.delete(exp)

    def transfer_file(self, experiment_name, src, dest):
        """
        scp for remote backends
        """
        raise NotImplementedError

    def login(self, experiment_name, *args, **kwargs):
        """
        ssh for remote backends
        """
        raise NotImplementedError

    def exec_command(self, experiment_name, process_name, command, *args, **kwargs):
        """
        command(array(string))
        """
        raise NotImplementedError

    # ========================================================
    # ===================== Query API ========================
    # ========================================================

    def list_experiments(self):
        """
        Returns:
            list of experiment names
        """
        raise NotImplementedError

    def describe_experiment(self, experiment_name):
        """
        Returns:
        {
            'pgroup1': {
                'p1': {'status': 'live', 'timestamp': '11:23'},
                'p2': {'status': 'dead'}
            },
            None: {  # always have all the processes
                'p3_lone': {'status': 'running'}
            }
        }
        Note: Return ordered dict to make sure things appear in order
        """
        raise NotImplementedError

    def describe_process_group(self,
                               experiment_name,
                               process_group_name):
        """
        Returns:
        {
            'p1': {'status': 'live', 'timestamp': '11:23'},
            'p2': {'status': 'dead'}
        }
        """
        raise NotImplementedError

    def describe_process(self,
                         experiment_name,
                         process_name,
                         process_group_name=None):
        """
        Returns:
            {'status: 'live', 'timestamp': '23:34'}
        """
        raise NotImplementedError

    def get_log(self, experiment_name, process_name, process_group=None,
                follow=False, since=0, tail=100, print_logs=False):
        """
        Returns output of the process <process_name> under experiment
        <experiment_name>
        Args:
            process_group(string): None if process is standalone
            follow(bool): set to True to wait for new logs
            since(int): the line to start getting logs from 
            tail(int): only get the last * lines of logs
            print_logs(bool): True to print logs to stdout
        """
        raise NotImplementedError

    def external_service(self, experiment_name, service_name):
        """
        returns an ip/dns address that can be used to visit a declared service
        Args:
            experiment_name: The experiment concerned
            service_name: the name of the service queried
        """
        raise NotImplementedError

    def find_process(self, experiment_name, process_name):
        """
        Finds a process with name <process_name> in experiment <experiment_name>
        Returns:
            [process_group] for all process_groups that contain a process with the given name
        """
        found = []
        exp = self.describe_experiment(experiment_name)
        for process_group_name, process_group in exp.items():
            for process in process_group:
                if process == process_name:
                    found.append(process_group_name)
        return found

    def set_experiment(self, experiment_name):
        """
        Args:
            experiment_name(str): to be set to default
        """
        raise NotImplementedError

    def current_experiment(self):
        """
        Returns experiment_name
        """
        raise NotImplementedError
    # ========================================================
    # ================= Helper functions =====================
    # ========================================================

    def fuzzy_match_experiment(self, name):
        """
        Fuzzy match experiment_name, precedence from high to low:
        1. exact match of <prefix + name>, if prefix option is turned on in ~/.surreal.yml
        2. exact match of <name> itself
        3. starts with <prefix + name>, sorted alphabetically
        4. starts with <name>, sorted alphabetically
        5. contains <name>, sorted alphabetically

        Returns:
            - string if the matching is exact
            - OR list of fuzzy matches
        """
        all_names = self.list_experiments()
        prefixed_name = self.prefix_username(name)
        if prefixed_name in all_names:
            return prefixed_name
        if name in all_names:
            return name
        # fuzzy matching
        matches = []
        matches += sorted([n for n in all_names if n.startswith(prefixed_name)])
        matches += sorted([n for n in all_names if n.startswith(name)])
        matches += sorted([n for n in all_names if name in n])
        matches = self._deduplicate_with_order(matches)
        return matches

    def prefix_username(self, name):
        username = SymphonyConfig().username
        if username is None:
            return name
        return username + '-' + name

    def _deduplicate_with_order(self, seq):
        """
        https://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-in-whilst-preserving-order
        deduplicate list while preserving order
        """
        return list(OrderedDict.fromkeys(seq))

