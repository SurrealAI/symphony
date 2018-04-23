from symphony_.spec import ProcessGroupSpec
from .process import KubeProcessSpec


class KubeProcessGroupSpec(ProcessGroupSpec):
    def _new_process(self, *args, **kwargs):
        return KubeProcessSpec(*args, **kwargs)

    @classmethod
    def from_dict(cls):
        pass

    def to_dict(self):
        pass
