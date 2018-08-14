import docker
from benedict import BeneDict
from symphony.engine import Cluster
from symphony.utils import runner
from symphony.utils.common import check_valid_project_name
from symphony.utils.common import split_docker_process_name
from .experiment import DockerExperimentSpec


_LABEL_PROJECT = 'com.docker.compose.project'


class DockerCluster(Cluster):
    def __init__(self):
        super().__init__()
        self.client = docker.from_env()

    # ========================================================
    # =================== Private Helpers ====================
    # ========================================================

    def _get_containers(self, exp_name, group_name=None, process_name=None):
        """
        Returns all Docker containers matching the given names.

        Args:
            exp_name: Name of the experiment
            process_name: Name of the process
            process_group_name: Name of the process group

        Returns:
            A list of docker.models.containers.Container objects that match
            the given names.

        """
        containers = []
        for c in self.client.containers.list():
            if (_LABEL_PROJECT in c.labels and
                c.labels[_LABEL_PROJECT] == exp_name):
                 _gn, _pn = split_docker_process_name(c.name[len(exp_name)+1:])
                 if group_name is None or group_name == _gn:
                     if process_name is None or process_name == _pn:
                         containers.append(c)
        if process_name:
            assert len(containers) in (0, 1), (
                    'Found two containers with the same exact name!')
        return containers

    def _container_info(self, c):
        """
        Extracts information from a container

        Args:
            c: a docker.models.containers.Container object

        Returns:
            a python dictionary with information about the specified container

        """
        return {
                'status': c.status,
                'id': c.id,
                'short_id': c.short_id,
                'image': {
                    'id': c.image.id,
                    'short_id': c.image.short_id,
                    'tags': c.image.tags,
                }
        }

    # ========================================================
    # ===================== Action API =======================
    # ========================================================

    def new_experiment(self, *args, **kwargs):
        return DockerExperimentSpec(*args, **kwargs)

    def launch(self, experiment_spec, dry_run=False):
        """
        Launches a Docker experiment specified by the given spec.

        Args:
            experiment_spec: a DockerExperimentSpec object
            dry_run: print out the generated YAML config instead of actually
                launching Docker containers.
        """
        print('Launching a Docker experiment', experiment_spec.name)
        launch_plan = experiment_spec.yml()

        if dry_run:
            print(launch_plan)
        else:
            compose_cmd = 'docker-compose -p {} -f - up -d'.format(
                    experiment_spec.name),
            out, err, retcode = runner.run_verbose(
                    compose_cmd, stdin=launch_plan)
            if retcode != 0:
                print('Error while starting Docker experiment')

    # ========================================================
    # ===================== Action API =======================
    # ========================================================

    def delete(self, exp_name, timeout=10):
        """
        Stops a running Docker experiment.

        Args:
            exp_name: Name of the experiment.
            timeout: Timeout in seconds to wait until we force stop
                each container before sending a SIGKILL.
        """
        print('Deleting a Docker experiment', exp_name)
        containers = self._get_containers(exp_name)
        for c in containers:
            c.stop(timeout=timeout)

    def delete_batch(self, experiments):
        for exp in experiments:
            self.delete(exp)

    def transfer_file(self, experiment_name, src_path, dest_path,
                      src_process=None, src_process_group=None,
                      dest_process=None, dest_process_group=None):
        raise NotImplementedError(
                'transfer_file is not implemented for Docker backend')

    def exec_command(self, experiment_name, process_name, command,
                     process_group_name=None, stream=False):
        """
        Executes a command inside the specified the Docker container
        for the specified Process.

        Args:
            exp_name: Name of the experiment
            process_name: Name of the process
            command: Command to run
            process_group_name: Name of the process group

        Returns:
            (return_code, output) tuple where output is
                - a bytes object if stream=False
                - a generator yielding response chunks if stream=True
        """
        containers = self._get_containers(experiment_name,
                                          group_name=process_group_name,
                                          process_name=process_name)
        if not containers:
            raise ValueError('No matching Process found')
        container = containers[0]
        retcode, output = container.exec_run(command, stream=stream)
        return retcode, output

    # ========================================================
    # ===================== Query API ========================
    # ========================================================

    def list_experiments(self):
        """
        Returns:
            The list of names of experiments that are currently running.
        """
        containers = self.client.containers.list()
        exp_names = set()
        for c in containers:
            if _LABEL_PROJECT in c.labels:
                exp_names.add(c.labels[_LABEL_PROJECT])
        return list(exp_names)

    def describe_experiment(self, exp_name):
        """
        Args:
            exp_name: Name of the experiment

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
        """
        containers = self._get_containers(exp_name)
        result = dict()
        for c in containers:
            grouped_name = c.name[len(exp_name)+1:]
            group_name, proc_name = split_docker_process_name(grouped_name)
            if group_name not in result:
                result[group_name] = dict()
            result[group_name][proc_name] = self._container_info(c)
        return result

    def describe_process_group(self,
                               exp_name,
                               process_group_name):
        """
        Args:
            exp_name: Name of the experiment
            process_group_name: Name of the process group

        Returns:
        {
            'p1': {'status': 'live', 'timestamp': '11:23'},
            'p2': {'status': 'dead'}
        }
        """
        containers = self._get_containers(exp_name,
                                          group_name=process_group_name)
        result = dict()
        for c in containers:
            grouped_name = c.name[len(exp_name)+1:]
            group_name, proc_name = split_docker_process_name(grouped_name)
            result[proc_name] = self._container_info(c)
        return result

    def describe_process(self,
                         exp_name,
                         process_name,
                         process_group_name=None):
        """
        Args:
            exp_name: Name of the experiment
            process_name: Name of the process
            process_group_name: Name of the process group

        Returns:
            {'status: 'live', 'timestamp': '23:34'}
        """
        containers = self._get_containers(exp_name,
                                          group_name=process_group_name,
                                          process_name=process_name)
        if containers:
            container = containers[0]
            grouped_name = container.name[len(exp_name)+1:]
            group_name, proc_name = split_docker_process_name(grouped_name)
            return self._container_info(container)

    def get_log(self, exp_name, process_name, process_group_name=None,
                follow=False, since=None, tail=None, print_logs=False):
        containers = self._get_containers(exp_name,
                                          group_name=process_group_name,
                                          process_name=process_name)
        if not containers:
            return ''
        container = containers[0]
        if follow:
            if print_logs:
                stream = container.logs(tail=tail, since=since, stream=True,
                                        follow=True)
                while True:
                    print(stream.next())
            else:
                raise ValueError(
                'Setting follow=True makes get_log a blocking call that '
                'streams the log to stdout. Did you mean to also set '
                'print_logs=True ?')
        else:
            log = container.logs(tail=tail, since=since)
            if print_logs:
                print(log.decode('utf-8'))
            return log


