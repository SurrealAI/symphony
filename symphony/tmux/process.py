from symphony.spec import ProcessSpec


class TmuxProcessSpec(ProcessSpec):
    def __init__(self, name, cmd):
        super().__init__(name)

    @classmethod
    def load_dict(cls):
        pass

    def dump_dict(self):
        pass
