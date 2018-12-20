import os

from symphony.spec import ProcessGroupSpec
from .process import SubprocProcessSpec


class SubprocProcessGroupSpec(ProcessGroupSpec):
    _ProcessClass = SubprocProcessSpec

    def __init__(self, name):
        """
        Args:
            name: name of the subprocess group
        """
        assert ':' not in name, 'name cannot contain ":"'
        super().__init__(name)
