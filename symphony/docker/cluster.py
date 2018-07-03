from benedict import BeneDict
from symphony.engine import Cluster
from symphony.utils import runner
from symphony.utils.common import check_valid_project_name
from .experiment import DockerExperimentSpec


class DockerCluster(Cluster):
    def __init__(self):
        super().__init__()

    # ========================================================
    # ===================== Action API =======================
    # ========================================================

    def new_experiment(self, *args, **kwargs):
        return DockerExperimentSpec(*args, **kwargs)

    def launch(self, experiment_spec, force=False, dry_run=False):
        print('Launching Docker experiment', experiment_spec.name)
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

    def delete(self, experiment_spec):
        launch_plan = experiment_spec.yml()
        compose_cmd = 'docker-compose -p {} -f - stop'.format(
                experiment_spec.name),
        out, err, retcode = runner.run_verbose(
                compose_cmd, stdin=launch_plan)
        if retcode != 0:
            print('Error while stopping Docker experiment')

    def delete_batch(self, experiments):
        for exp in experiments:
            self.delete(exp)

    def transfer_file(self, experiment_name, src_path, dest_path,
                      src_process=None, src_process_group=None,
                      dest_process=None, dest_process_group=None):
        raise NotImplementedError(
                'transfer_file is not implemented for Docker Compose backend')

    def exec_command(self, experiment_name, process_name, command, process_group_name=None):
        raise NotImplementedError

    # ========================================================
    # ===================== Query API ========================
    # ========================================================

    def list_experiments(self):
        """
        Returns:
            list of experiment names
        """
        cmd = ('docker ps --filter "{}" -q | ' +
               'xargs docker inspect --format=\'{{{{{}}}}}\' | ' +
               'uniq').format(
                       'label=com.docker.compose.project',
                       'index .Config.Labels "com.docker.compose.project"')
        out, err, retcode = runner.run(cmd)
        if retcode != 0:
            print('Error while fetching Docker experiments')
            return []
        exp_names = out.split('\n')
        return exp_names

    # def describe_headers(self):
    #     return ['Ready', 'Restarts', 'State']

    def describe_experiment(self, experiment_name):
        """
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
        raise NotImplementedError
        # check_valid_project_name(experiment_name)
        # cmd = ('docker ps -q -f label=com.docker.compose.project={} | ' +
        #        'xargs docker inspect --format="{{{{index .Name}}}}"').format(
        #                experiment_name)
        # out, err, retcode = runner.run(cmd)
        # if retcode != 0:
        #     print('Error while fetching Docker experiments')
        #     return {}
        # print(out)


    def describe_process_group(self,
                               experiment_name,
                               process_group_name):
        """
        Returns:
        {
            'p1': {'status': 'live', 'timestamp': '11:23'},
            'p2': {'status': 'dead'}
        }
        """
        raise NotImplementedError

    def describe_process(self,
                         experiment_name,
                         process_name,
                         process_group_name=None):
        """
        Returns:
            {'status: 'live', 'timestamp': '23:34'}
        """
        raise NotImplementedError

    def get_log(self, experiment_name, process_name, process_group=None,
                follow=False, since=0, tail=500, print_logs=False):
        raise NotImplementedError

