import shlex
from datetime import datetime
from pathlib import Path
from collections import OrderedDict
from benedict import BeneDict
from benedict.data_format import load_yaml_str, load_json_str
from symphony.engine import Cluster
from symphony.addons import LocalFileManager
from symphony.utils.common import check_valid_dns, is_sequence
import symphony.utils.runner as runner
from .experiment import KubeExperimentSpec


_RESERVED_NS = ['default', 'kube-public', 'kube-system']


class KubeCluster(Cluster):
    def __init__(self):
        super().__init__()
        self.fs = LocalFileManager()

    def new_experiment(self, *args, **kwargs):
        return KubeExperimentSpec(*args, **kwargs)

    def launch(self, experiment_spec, force=False, dry_run=False):
        print('launching', experiment_spec.name)
        launch_plan = experiment_spec.compile()

        if dry_run:
            print(launch_plan)
        else:
            # TODO: some of them should be shared
            if self.fs.has_experiment_folder():
                if not force and self.fs.experiment_exists(experiment_spec.name):
                    raise ValueError('[Error] Experiment {} already exists'.format(experiment_spec.name))
                experiment_file = Path(self.fs.save_experiment(experiment_spec))
                experiment_folder = experiment_file.parent
                launch_plan_file = experiment_folder / 'kube.yml'
                with launch_plan_file.open('w') as f:
                    f.write(launch_plan)
                #TODO: persist yaml file
                runner.run_verbose('kubectl create namespace ' + experiment_spec.name)
                runner.run_verbose('kubectl create -f "{}" --namespace {}'.format(launch_plan_file, experiment_spec.name))
                self.set_experiment(experiment_spec.name)
            else:
                runner.run_verbose('kubectl create namespace ' + experiment_spec.name)
                runner.run_verbose('kubectl create -f - --namespace {}'.format(experiment_spec.name), stdin=launch_plan)
                self.set_experiment(experiment_spec.name)

    # ========================================================
    # ===================== Action API =======================
    # ========================================================

    def delete(self, experiment_name):
        assert experiment_name not in _RESERVED_NS, \
            'cannot delete reserved names: default, kube-public, kube-system'
        check_valid_dns(experiment_name)
        runner.run_verbose(
            'kubectl delete namespace {}'.format(experiment_name),
            print_out=True, raise_on_error=False)

    # def delete_batch(self, experiments):

    def transfer_file(self, experiment_name, src_path, dest_path,
                      src_process=None, src_process_group=None,
                      dest_process=None, dest_process_group=None):
        """
        scp for remote backends:
        """
        src_filepath = self._format_scp_path(src_process, src_process_group, src_path)
        dest_filepath = self._format_scp_path(dest_process, dest_process_group, dest_path)
        cmd = 'kubectl cp {} {} {}'.format(src_filepath, dest_filepath,
                                           self._get_ns_cmd(experiment_name))
        runner.run_raw(cmd, print_cmd=True)

    def _format_scp_path(self, pg, p, path):
        if p is None:
            return path
        else:
            if pg is None:
                pg = p
            return '{}:{} -c {}'.format(pg, path, p)

    def login(self, experiment_name, process_name, process_group_name=None):
        """
        ssh for remote backends
        """
        self.exec_command(experiment_name, process_name, 'bash', process_group_name)

    def exec_command(self, experiment_name, process_name, command, process_group_name=None):
        """
        kubectl exec -ti

        Args:

        Returns:
            stdout string if is_print else None
        """
        if is_sequence(command):
            command = ' '.join(map(shlex.quote, command))
        ns_cmd = self._get_ns_cmd(experiment_name)
        if process_group_name is None:
            pod_name, container_name = process_name, process_name
        else:
            pod_name, container_name = process_group_name, process_name
        return runner.run_raw('kubectl exec -ti {} -c {} {} -- {}'.format(pod_name,
                              container_name, ns_cmd, command))

    # ========================================================
    # ===================== Query API ========================
    # ========================================================

    def list_experiments(self):
        """
        Returns:
            list of experiment names
        """
        all_names = self.query_resources('namespace', output_format='name')
        # names look like namespace/<actual_name>, need to postprocess
        all_namespaces = [n.split('/')[-1] for n in all_names]
        filtered_namespaces = [x for x in all_namespaces if x not in _RESERVED_NS]
        return filtered_namespaces

    def describe_headers(self):
        return ['Ready', 'Restarts', 'State']

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
        all_processes = BeneDict(self.query_resources('pod', output_format='json',
                                                      namespace=experiment_name))
        out = OrderedDict()
        for pod in all_processes.items:
            pod_name = pod.metadata.name
            if 'containerStatuses' in pod.status: # Pod is created
                container_statuses = self._parse_container_statuses(
                    pod.status.containerStatuses)
                # test if the process is stand-alone
                if len(container_statuses) == 1 and list(container_statuses.keys())[0] == pod_name:
                    if not None in out:
                        out[None] = OrderedDict()
                    out[None][pod_name] = container_statuses[pod_name]
                else:
                    out[pod_name] = container_statuses
            else:
                out[pod_name] = {'~': self._parse_unstarted_pod_statuses(pod.status)}
        return out

    def _parse_unstarted_pod_statuses(self, data):
        out = OrderedDict([
            ('Ready', '0'),
            ('Restarts', '0'),
            ('State', 'Pending')
        ])
        return out

    def _parse_container_statuses(self, status_list):
        out = OrderedDict()
        for container_status in status_list:
            container_name = container_status.name
            state = list(container_status.state.keys())[0]
            state_info = container_status.state[state]
            out[container_name] = OrderedDict([
                ('Ready', str(int(container_status.ready))),
                ('Restarts', str(int(container_status.restartCount))),
                ('State', self._parse_container_state_info(state, state_info))
            ])
        return out

    def _parse_container_state_info(self, state, state_info):
        if state == 'waiting':
            return 'waiting: {}'.format(state_info.reason)
        elif state == 'running':
            return 'running: {}'.format(self._get_age(state_info.startedAt))
        elif state == 'completed' or state == 'terminated':
            return '{} ({}) after {}: {}' \
                .format(state,
                        state_info.exitCode,
                        self._get_age(state_info.startedAt, state_info.finishedAt),
                        state_info.reason)
        else:
            print('UNKONWN state:', state, state_info)

    def _get_age(self, start_time_str, finish_time_str=None):
        """
        Args:
            start_time_str: ISO time string '%Y-%m-%dT%H:%M:%SZ' for start time
            finish_time_str: ISO time string or UTC now
        """
        start_time = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M:%SZ')
        if finish_time_str:
            finish_time = datetime.strptime(finish_time_str, '%Y-%m-%dT%H:%M:%SZ')
        else:
            finish_time = datetime.utcnow()
        return self._format_time_delta(finish_time - start_time)

    def _format_time_delta(self, delta):
        seconds = abs(delta.seconds)
        days = abs(delta.days)
        if days:
            hrs = seconds // 3600
            return '{}d{}h'.format(days, hrs)
        else:
            minutes = seconds // 60
            hrs = seconds / 3600
            if seconds < 60:
                return '{}s'.format(seconds)
            elif seconds < 3600:
                return '{}m'.format(minutes)
            else:
                return '{:.1f}h'.format(hrs)

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
        res = self.query_resources('pod', names=[process_group_name],
                                   output_format='json',
                                   namespace=experiment_name)
        if not res:
            raise ValueError('Cannot find process_group {} in experiment {}' \
                .format(process_group_name, experiment_name))
        pod = BeneDict(res)
        return self._parse_container_statuses(pod.status.containerStatuses)

    def describe_process(self,
                         experiment_name,
                         process_name,
                         process_group_name=None):
        """
        Returns:
            {'status: 'live', 'timestamp': '23:34'}
        """
        if process_group_name is not None:
            pg = self.describe_process_group(experiment_name, process_group_name)
            return pg[process_name]
        else: # standalone process is in a pod with name same as its process group
            pg = self.describe_process_group(experiment_name, process_name)
            return pg[process_name]

    def get_log(self, experiment_name, process_name, process_group=None,
                follow=False, since=0, tail=500, print_logs=False):
        if process_group is None:
            pod_name, container_name = process_name, process_name
        else:
            pod_name, container_name = process_group, process_name

        cmd = self._get_logs_cmd(
            pod_name, process_name, follow=follow,
            since=since, tail=tail, namespace=experiment_name
        )
        if follow:  # os.system will not block, stream the latest logs to stdout
            runner.run_raw(cmd)
        else:
            out, err, retcode = runner.run_verbose(
                cmd,
                print_out=print_logs,
                raise_on_error=False
            )
            if retcode != 0:
                return ''
            else:
                return out

    def external_url(self, experiment_name, service_name):
        res = BeneDict(self.query_resources('svc', 'yaml',
                                  names=[service_name], namespace=experiment_name))
        conf = res.status.loadBalancer
        if not ('ingress' in conf and 'ip' in conf.ingress[0]):
            raise ValueError('Service {} not found in experiment {}'.format(service_name, experiment_name))
        ip = conf.ingress[0].ip
        port = res.spec.ports[0].port
        return '{}:{}'.format(ip, port)

    ### other

    def current_context(self):
        out, err, retcode = runner.run_verbose(
            'kubectl config current-context', print_out=False, 
            raise_on_error=True)
        return out

    def current_experiment(self):
        """
        Parse from `kubectl config view`
        """
        config = self.config_view()
        current_context = self.current_context()
        for context in config['contexts']:
            if context['name'] == current_context:
                return context['context']['namespace']
        raise RuntimeError('INTERNAL: current context not found')

    def set_experiment(self, namespace):
        """
        https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/
        After this call, all subsequent `kubectl` will default to the namespace
        """
        check_valid_dns(namespace)
        _, _, retcode = runner.run_verbose(
            'kubectl config set-context $(kubectl config current-context) --namespace={}'.format(namespace),
            print_out=True, raise_on_error=False)
        if retcode == 0:
            print('successfully switched to namespace `{}`'.format(namespace))

    def _get_selectors(self, labels, fields):
        """
        Helper for list_resources and list_jsonpath
        """
        labels, fields = labels.strip(), fields.strip()
        cmd= ' '
        if labels:
            cmd += '--selector ' + shlex.quote(labels)
        if fields:
            cmd += ' --field-selector ' + shlex.quote(fields)
        return cmd

    def query_resources(self, resource,
                        output_format,
                        names=None,
                        labels='',
                        fields='',
                        namespace=None):
        """
        Query all items in the resource with `output_format`
        JSONpath: https://kubernetes.io/docs/reference/kubectl/jsonpath/
        label selectors: https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/

        Args:
            resource: pod, service, deployment, etc.
            output_format: https://kubernetes.io/docs/reference/kubectl/overview/#output-options
              - custom-columns=<spec>
              - custom-columns-file=<filename>
              - json: returns a dict
              - jsonpath=<template>
              - jsonpath-file=<filename>
              - name: list
              - wide
              - yaml: returns a dict
            names: list of names to get resource, mutually exclusive with
                label and field selectors. Should only specify one.
            labels: label selector syntax, comma separated as logical AND. E.g:
              - equality: mylabel=production
              - inequality: mylabel!=production
              - set: mylabel in (group1, group2)
              - set exclude: mylabel notin (group1, group2)
              - don't check value, only check key existence: mylabel
              - don't check value, only check key nonexistence: !mylabel
            fields: field selector, similar to label selector but operates on the
              pod fields, such as `status.phase=Running`
              fields can be found from `kubectl get pod <mypod> -o yaml`

        Returns:
            dict if output format is yaml or json
            list if output format is name
            string from stdout otherwise
        """
        if names and (labels or fields):
            raise ValueError('names and (labels or fields) are mutually exclusive')
        cmd = 'kubectl get ' + resource
        cmd += self._get_ns_cmd(namespace)
        if names is None:
            cmd += self._get_selectors(labels, fields)
        else:
            assert isinstance(names, (list, tuple))
            cmd += ' ' + ' '.join(names)
        if '=' in output_format:
            # quoting the part after jsonpath=<...>
            prefix, arg = output_format.split('=', 1)
            output_format = prefix + '=' + shlex.quote(arg)
        cmd += ' -o ' + output_format
        out, _, _ = runner.run_verbose(cmd, print_out=False, raise_on_error=True)
        if output_format == 'yaml':
            return load_yaml_str(out)
        elif output_format == 'json':
            return load_json_str(out)
        elif output_format == 'name':
            return out.split('\n')
        else:
            return out

    def query_jsonpath(self, resource,
                       jsonpath,
                       names=None,
                       labels='',
                       fields='',
                       namespace=''):
        """
        Query items in the resource with jsonpath
        https://kubernetes.io/docs/reference/kubectl/jsonpath/
        This method is an extension of list_resources()
        Args:
            resource:
            jsonpath: make sure you escape dot if resource key string contains dot.
              key must be enclosed in *single* quote!!
              e.g. {.metadata.labels['kubernetes\.io/hostname']}
              you don't have to do the range over items, we take care of it
            labels: see `list_resources`
            fields:

        Returns:
            a list of returned jsonpath values
        """
        if '{' not in jsonpath:
            jsonpath = '{' + jsonpath + '}'
        if names is not None and len(names) == 1:
            jsonpath = jsonpath
        else:
            jsonpath = '{range .items[*]}' + jsonpath + '{"\\n\\n"}{end}'
        output_format = "jsonpath=" + jsonpath
        out = self.query_resources(
            resource=resource,
            names=names,
            output_format=output_format,
            labels=labels,
            fields=fields,
            namespace=namespace
        )
        return out.split('\n\n')

    def config_view(self):
        """
        kubectl config view
        Generates a yaml of context and cluster info
        """
        out, err, retcode = runner.run_verbose(
            'kubectl config view', print_out=False, raise_on_error=True)
        return BeneDict(load_yaml_str(out))

    def _get_ns_cmd(self, namespace):
        if namespace:
            return ' --namespace ' + namespace
        else:
            return ''

    def _get_logs_cmd(self, pod_name, container_name,
                      follow, namespace, since=0, tail=-1):
        return 'kubectl logs {} {} {} --since={} --tail={}{}'.format(
            pod_name,
            container_name,
            '--follow' if follow else '',
            since,
            tail,
            self._get_ns_cmd(namespace)
        )
