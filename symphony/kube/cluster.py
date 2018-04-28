from symphony.engine import Cluster
from .experiment import KubeExperimentSpec
import symphony.utils.runner as runner
from benedict.data_format import load_yaml_str, load_json_str
from benedict import BeneDict
import shlex


class KubeCluster(Cluster):
    def __init__(self, dry_run=False):
        self.dry_run = dry_run

    def new_experiment(self, *args, **kwargs):
        return KubeExperimentSpec(*args, **kwargs)

    def launch(self, experiment_spec):
        print('launching', experiment_spec)
        launch_plan = experiment_spec.compile()

        if self.dry_run:
            print(launch_plan)
        else:
            # TODO: some of them should be shared
            self.set_namespace(experiment.name)
            self.fs.save_experiment(experiment)
            launch_plan_file = self.fs.save_launch_plan(experiment.name, launch_plan, 'kubernetes')
            #TODO: persist yaml file
            runner.run_verbose('kubectl create namespace ' + experiment.name, dry_run=self.dry_run)
            runner.run_verbose('kubectl create -f "{}" --namespace {}'.format(launch_plan_file, experiment.name), dry_run=self.dry_run)

    # ========================================================
    # ===================== Action API =======================
    # ========================================================    

    def delete(self, experiment_name):
        check_valid_dns(experiment_name)
        runner.run_verbose(
            'kubectl delete namespace {}'.format(experiment_name),
            print_out=True, raise_on_error=False
        )

    # def delete_batch(self, experiments):

    def transfer_file(self, experiment_name, src, dest):
        """
        scp for remote backends:
        """
        src_name, src_path = self._format_scp_path(src_file, experiment_name)
        dest_name, dest_path = self._format_scp_path(dest_file, experiment_name)
        assert (src_name is None) != (dest_name is None), \
            '[Error] one of "src_file" and "dest_file" must be remote and the other local.'
        cmd = 'kubectl cp {} {} {}'.format(src_path, dest_path, self._get_ns_cmd(experiment_name))
        runner.run_raw(cmd, print_cmd=True, dry_run=self.dry_run)

    def _format_scp_path(self, f, experiment_name):
        if ':' in f:
            path_name, path = f.split(':')
            if path_name.find('/'):
                assert len(path_name.split('/')) == 2, 'Invalid process name {}'.format(path_name)
                pod, container = path_name.split('/')
            else:
                pod, container = path_name
            return process_name, '{}:{} -c {}'.format(pod, path, container)
        else:
            return None, f

    def login(self, experiment_name, process_name, process_group_name=None):
        """
        ssh for remote backends
        """
        self.exec(experiment_name, process_name, 'bash', process_group_name)

    def exec_command(self, experiment_name, process_name, command, process_group_name=None):
        """
        kubectl exec -ti

        Args: 
        
        Returns:
            stdout string if is_print else None
        """
        if is_sequence(cmd):
            cmd = ' '.join(map(shlex.quote, cmd))
        ns_cmd = self._get_ns_cmd(experiment_name)
        if process_group_name is None:
            pod_name, container_name = process_name, process_name
        else:
            pod_name, container_name = process_name, process_group_name
        return runner.run_raw('kubectl exec -ti {} -c {} {} -- {}'.format(pod_name, 
                container_name, ns_cmd, cmd), dry_run=self.dry_run)

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
        return [n.split('/')[-1] for n in all_names]

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
        all_processes = BeneDict(self.query_resources('pod',output_format='json',
                                            namespace=experiment_name))
        out = BeneDict()
        for pod in all_processes.items:
            pod_name = pod.metadata.name
            container_statuses = self._parse_container_statuses(
                                    pod.status.containerStatuses,
                                    pod.status.startTime)
            # test if the process is stand-alone
            if len(container_statuses) == 1 and list(container_statuses.keys())[0] == pod_name:
                if not None in out:
                    out[None] = BeneDict()
                out[None][pod_name] = container_statuses[pod_name]
            else:
                out[pod_name] = container_statuses
        return out

    def _parse_container_statuses(self, li, pod_start_time):
        out = {}
        for container_status in li:
            container_name = container_status.name
            assert(len(container_status.state.keys()) == 1)
            state = list(container_status.state.keys())[0]
            state_info = container_status.state[state]
            out[container_name] = BeneDict({
                'state': state,
                'ready': container_status.ready,
                'restartCount': container_status.restartCount,
                'start_time': pod_start_time,
                'state_info': state_info
            })
        return out

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
        res = self.query_resources('pod',names=[process_group_name],output_format='json',
                                            namespace=experiment_name)
        if not res:
            raise ValueError('Cannot find process_group {} in experiment {}'.format(process_group_name, experiment_name))
        pod = BeneDict(res)
        return self._parse_container_statuses(pod.status.containerStatuses,
                                              pod.status.startTime)

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

    def get_stdout(self, experiment, process, process_group=None, since=0, tail=100):
        if process_group is None:
            pod_name, container_name = process, process
        else:
            pod_name, container_name = process, process_group
        out, err, retcode = runner.run_verbose(
            self._get_logs_cmd(
                pod_name, process_name, follow=False,
                since=since, tail=tail, namespace=experiment_name
            ),
            print_out=False,
            raise_on_error=True,
            dry_run=self.dry_run
        )
        if retcode != 0:
            return ''
        else:
            return out

    def get_stderr(self, experiment, process, process_group=None, since=0, tail=100):
        self.get_stdout(experiment, process, process_group)

    def external_service(self, experiment_name, service_name):
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
            raise_on_error=True, dry_run=self.dry_run
        )
        return out

    def current_experiment(self):
        """
        Parse from `kubectl config view`
        """
        config = self.config_view()
        current_context = self.current_context()
        if self.dry_run:
            return 'dummy-namespace'
        for context in config['contexts']:
            if context['name'] == current_context:
                return context['context']['namespace']
        raise RuntimeError('INTERNAL: current context not found')

    def set_namespace(self, namespace):
        """
        https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/
        After this call, all subsequent `kubectl` will default to the namespace
        """
        check_valid_dns(namespace)
        _, _, retcode = runner.run_verbose(
            'kubectl config set-context $(kubectl config current-context) --namespace={}'.format(namespace),
            print_out=True, raise_on_error=False, dry_run=self.dry_run
        )
        if not self.dry_run and retcode == 0:
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
        out, _, _ = runner.run_verbose(cmd, print_out=False, raise_on_error=True, dry_run=self.dry_run)
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
            'kubectl config view', print_out=False, 
            raise_on_error=True, dry_run=self.dry_run
        )
        return BeneDict.loads_yaml(out)

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
