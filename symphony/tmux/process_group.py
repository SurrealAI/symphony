from symphony.spec import ProcessGroupSpec
from .process import TmuxProcessSpec


class TmuxProcessGroupSpec(ProcessGroupSpec):
    def _new_process(self, *args, **kwargs):
        return TmuxProcessSpec(*args, **kwargs)

    @classmethod
    def from_dict(cls):
        pass

    def to_dict(self):
        pass
