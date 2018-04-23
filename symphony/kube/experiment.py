from symphony.spec import ExperimentSpec
from .process import KubeProcessSpec
from .process_group import KubeProcessGroupSpec


class KubeExperimentSpec(ExperimentSpec):
    def _new_process(self, *args, **kwargs):
        return KubeProcessSpec(*args, **kwargs)

    def _new_process_group(self, *args, **kwargs):
        return KubeProcessGroupSpec(*args, **kwargs)

    @classmethod
    def from_dict(cls):
        pass

    def to_dict(self):
        pass
