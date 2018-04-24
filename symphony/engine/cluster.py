"""
Cluster subclasses are the actual execution engines
"""

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

    def launch(self, experiment_config):
        raise NotImplementedError

    def launch_batch(self, experiment_configs):
        for exp in experiment_configs:
            self.launch(exp)

    # ========================================================
    # ===================== Action API =======================
    # ========================================================
    def delete(self, experiment_name):
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

    def exec_command(self, experiment_name, *args, **kwargs):
        raise NotImplementedError

    # ========================================================
    # ===================== Query API ========================
    # ========================================================
    def list_experiments(self):
        raise NotImplementedError

    def fuzzy_match_experiments(self):
        # TODO
        pass

    def list_process_groups(self, experiment_name):
        raise NotImplementedError

    def list_processes(self, experiment_name, process_group=None):
        raise NotImplementedError

    def status(self, experiment_name, process_name, process_group=None):
        raise NotImplementedError

    def get_stdout(self, experiment_name, process_name, process_group=None):
        raise NotImplementedError

    def get_stderr(self, experiment_name, process_name, process_group=None):
        raise NotImplementedError
