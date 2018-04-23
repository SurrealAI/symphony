"""
Cluster subclasses are the actual execution engines
"""

_BACKEND_REGISTRY = {}


class _BackendRegistry:
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

    # ========================================================
    # ===================== Action API =======================
    # ========================================================

    # ========================================================
    # ===================== Query API ========================
    # ========================================================

