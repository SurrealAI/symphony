import os
import copy
from symphony.spec import ExperimentSpec
from symphony.utils.common import compact_range_dumps, compact_range_loads
from symphony.utils.common import print_err
from symphony.engine import AddressBook
from .common import tmux_name_check
from .process import TmuxProcessSpec
from .process_group import TmuxProcessGroupSpec


class TmuxExperimentSpec(ExperimentSpec):
    _ProcessClass = TmuxProcessSpec
    _ProcessGroupClass = TmuxProcessGroupSpec

    def __init__(self, name, start_dir=None, preamble_cmds=None, port_range=None):
        """
        Args:
            name: name of the Experiment
            start_dir: directory where new processes start for this Experiment
            preamble_cmds: str or list of str containing commands to run in each
                process before the actual command (e.g. `source activate py3`)
        """
        # Valid session name is not empty and doesn't contain colon or period.
        # (reference: https://github.com/tmux/tmux/blob/master/session.c)
        tmux_name_check(name, 'Experiment')
        super().__init__(name)
        if preamble_cmds is None:
            preamble_cmds = []
        self.start_dir = os.path.expanduser(start_dir or '.')
        self.set_preamble_cmds(preamble_cmds)

        if port_range is None:
            port_range = list(range(7000, 9000))
        self.port_range = list(port_range)
        self.exposed_services = {}
        self.binded_services = {}

    def set_preamble_cmds(self, preamble_cmds):
        if not isinstance(preamble_cmds, (tuple, list)):
            self.preamble_cmds = [preamble_cmds]
            print_err(('[Warning] preamble command "{}" for TmuxExperiment ' +
                       '"{}" should be a list').format(preamble_cmds, name))
        else:
            self.preamble_cmds = list(preamble_cmds)

    def _new_process(self, *args, **kwargs):
        if 'start_dir' not in kwargs:
            kwargs['start_dir'] = self.start_dir
        return TmuxProcessSpec(*args, **kwargs)

    def _new_process_group(self, *args, **kwargs):
        if 'start_dir' not in kwargs:
            kwargs['start_dir'] = self.start_dir
        return TmuxProcessGroupSpec(*args, **kwargs)

    def compile(self):
        """
        Compile necessary information before launch
        """
        self.address_book = AddressBook()

        self.declare_services()
        self.assign_addresses()

    def assign_addresses(self):
        for exposed_service_name in self.exposed_services:
            port = self.exposed_services[exposed_service_name]
            self.address_book.add_entry(exposed_service_name, '127.0.0.1', port)
        for binded_service_name in self.binded_services:
            port = self.binded_services[binded_service_name]
            self.address_book.add_entry(binded_service_name, '127.0.0.1', port)
        env_dict = self.address_book.dump()
        for process in self.list_all_processes():
            process.set_envs(env_dict)

    def declare_services(self):
        """
            Loop through all processes and assign addresses for all declared ports
        """
        exposed = {}
        binded = {}
        port_range = copy.deepcopy(self.port_range)
        for process in self.list_all_processes():
            for exposed_service_name in process.exposed_services:
                port = process.exposed_services[exposed_service_name]
                exposed[exposed_service_name] = port
                if port in self.port_range:
                    port_range.remove(port)

            for binded_service_name in process.binded_services:
                port = process.binded_services[binded_service_name]
                binded[binded_service_name] = port
                if port in self.port_range:
                    port_range.remove(port)

        for exposed_service_name, port in exposed.items():
            if port is None:
                port = self.get_port(port_range)
            self.exposed_services[exposed_service_name] = port
        for binded_service_name, port in binded.items():
            if port is None:
                port = self.get_port(port_range)
            self.binded_services[binded_service_name] = port
        self.validate_connect()

    def validate_connect(self):
        """
        Check if all connected services are correctly provided
        """
        for process in self.list_all_processes():
            for connected_service_name in process.connected_services:
                if connected_service_name not in self.binded_services:
                    raise ValueError('Service {} is connected by process {} but not binded' \
                                     .format(connected_service_name, process.name))

    # TODO: factor code
    def get_port(self, port_range):
        if len(port_range) == 0:
            raise ValueError('[Error] Experiment {} ran out of ports on Tmux.' \
                                .format(self.name))
        return port_range.pop(0)

    def _load_dict(self, di):
        super()._load_dict(di)
        self.port_range = compact_range_loads(di['port_range'])
        self.start_dir = di['start_dir']
        self.preamble_cmds = di['preamble_cmds']

    def dump_dict(self):
        data = super().dump_dict()
        data['port_range'] = compact_range_dumps(self.port_range)
        data['start_dir'] = self.start_dir
        data['preamble_cmds'] = self.preamble_cmds
        return data
