from symphony.spec import ExperimentSpec
from .process import TmuxProcessSpec
from .process_group import TmuxProcessGroupSpec


class TmuxExperimentSpec(ExperimentSpec):
    def _new_process(self, *args, **kwargs):
        return TmuxProcessSpec(*args, **kwargs)

    def _new_process_group(self, *args, **kwargs):
        return TmuxProcessGroupSpec(*args, **kwargs)

    @classmethod
    def load_dict(cls):
        pass

    def dump_dict(self):
        pass
