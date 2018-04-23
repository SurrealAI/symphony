from symphony.cluster.cluster import Cluster
from symphony.cluster_config.kubernetes import *
from symphony.core.address import AddressBookData
from symphony.core.fs_manager import FSManager
from symphony.core.application_config import SymphonyConfig
from symphony.utils.common import check_valid_dns, is_sequence
import symphony.utils.commandline as cmdline
import shlex
from benedict import BeneDict
import yaml
import collections
import itertools
from io import StringIO


class KubeCluster(Cluster):
    # TODO: make launch work
    # TODO: username scoping
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.fs = FSManager()

    def launch(self, experiment): # TODO: partial launch
        kube_exp = experiment.cluster_configs.get('kubernetes', None)
        if kube_exp is None:
            kube_exp = KubeExperiment(experiment)
            experiment.cluster_configs['kubernetes'] = kube_exp
        launch_plan = kube_exp.compile()

        if self.dry_run:
            print(launch_plan)
        else:
            self.set_namespace(experiment.name)
            self.fs.save_experiment(experiment)
            launch_plan_file = self.fs.save_launch_plan(experiment.name, launch_plan, 'kubernetes')
            #TODO: persist yaml file
            cmdline.run_verbose('kubectl create namespace ' + experiment.name, dry_run=self.dry_run)
            cmdline.run_verbose('kubectl create -f "{}" --namespace {}'.format(launch_plan_file, experiment.name), dry_run=self.dry_run)
    

    def delete(self, experiment_name):
        """
        kubectl delete -f kurreal.yml --namespace <experiment_name>
        kubectl delete namespace <experiment_name>

        Notes:
            Delete a namespace will automatically delete all resources under it.

        Args:
            namespace
            yaml_path: if None, delete the namespace.
        """
        check_valid_dns(experiment_name)
        cmdline.run_verbose(
            'kubectl delete namespace {}'.format(experiment_name),
            print_out=True, raise_on_error=False
        )
        # if yaml_path: TODO: sometime add this functionality in?
        #     if not U.f_exists(yaml_path) and not self.dry_run:
        #         raise FileNotFoundError(yaml_path + ' does not exist, cannot stop.')
        #     self.run_verbose(
        #         'delete -f "{}" --namespace {}'
        #             .format(yaml_path, namespace),
        #         print_out=True, raise_on_error=False
        #     )
        

    def current_context(self):
        out, err, retcode = cmdline.run_verbose(
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

    def list_experiments(self):
        all_names = self.query_resources('namespace', output_format='name')
        # names look like namespace/<actual_name>, need to postprocess
        return [n.split('/')[-1] for n in all_names]

    def set_namespace(self, namespace):
        """
        https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/
        After this call, all subsequent `kubectl` will default to the namespace
        """
        check_valid_dns(namespace)
        _, _, retcode = cmdline.run_verbose(
            'kubectl config set-context $(kubectl config current-context) --namespace={}'.format(namespace),
            print_out=True, raise_on_error=False, dry_run=self.dry_run
        )
        if not self.dry_run and retcode == 0:
            print('successfully switched to namespace `{}`'.format(namespace))

    def _deduplicate_with_order(self, seq):
        """
        https://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-in-whilst-preserving-order
        deduplicate list while preserving order
        """
        return list(collections.OrderedDict.fromkeys(seq))

    def prefix_username(self, name):
        print(name)
        return SymphonyConfig().experiment_name_prefix + '-' + name

    def fuzzy_match_experiment(self, name, max_matches=10):
        """
        Fuzzy match experiment_name, precedence from high to low:
        1. exact match of <prefix + name>, if prefix option is turned on in ~/.surreal.yml
        2. exact match of <name> itself
        3. starts with <prefix + name>, sorted alphabetically
        4. starts with <name>, sorted alphabetically
        5. contains <name>, sorted alphabetically
        Up to `max_matches` number of matches

        Returns:
            - string if the matching is exact
            - OR list of fuzzy matches
        """
        all_names = self.list_experiments()
        prefixed_name = self.prefix_username(name)
        if prefixed_name in all_names:
            return prefixed_name
        if name in all_names:
            return name
        # fuzzy matching
        matches = []
        matches += sorted([n for n in all_names if n.startswith(prefixed_name)])
        matches += sorted([n for n in all_names if n.startswith(name)])
        matches += sorted([n for n in all_names if name in n])
        matches = self._deduplicate_with_order(matches)
        return matches[:max_matches]

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
        out, _, _ = cmdline.run_verbose(cmd, print_out=False, raise_on_error=True, dry_run=self.dry_run)
        if output_format == 'yaml':
            return BeneDict.loads_yaml(out)
        elif output_format == 'json':
            return BeneDict.loads_json(out)
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
        out, err, retcode = cmdline.run_verbose(
            'kubectl config view', print_out=False, 
            raise_on_error=True, dry_run=self.dry_run
        )
        return BeneDict.loads_yaml(out)

    def external_ip(self, service_name, experiment_name=None):
        """
        Returns:
            "<ip>:<port>": if service is found
            None: otherwise
        """
        if experiment_name is None:
            experiment_name = self.current_experiment()
        res = self.query_resources('svc', 'yaml',
                                  names=[service_name], namespace=experiment_name)
        conf = res.status.loadBalancer
        if not ('ingress' in conf and 'ip' in conf.ingress[0]):
            return None
        ip = conf.ingress[0].ip
        port = res.spec.ports[0].port
        return '{}:{}'.format(ip, port)

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

    def get_pod_container(self, experiment_name, process_name):
        experiment = self.fs.load_experiment(experiment_name)
        for process in experiment.processes.values():
            if process.name == process_name:
                if process.process_group is not None:
                    pod_name = process.process_group.name
                else:
                    pod_name = process.name
                return pod_name, process_name
        raise ValueError('[Error] Cannot find processs with name: {}'.format(process_name))

    def logs(self,process_name, since=0,tail=100,experiment_name=None):
        """
        kubectl logs <pod_name> <container_name> --follow --since= --tail=
        https://kubernetes-v1-4.github.io/docs/user-guide/kubectl/kubectl_logs/

        Returns:
            stdout string
        """
        if experiment_name is None:
            experiment_name = self.current_experiment()
        pod_name, container_name = self.get_pod_container(experiment_name, process_name)
        out, err, retcode = cmdline.run_verbose(
            self._get_logs_cmd(
                pod_name, process_name, follow=False,
                since=since, tail=tail, namespace=experiment_name
            ),
            print_out=False,
            raise_on_error=False,
            dry_run=self.dry_run
        )
        if retcode != 0:
            return ''
        else:
            return out

    def logs_print(self,process_name,follow=False,
                since=0,tail=100,experiment_name=None):
        """
        kubectl logs <pod_name> <container_name> --follow --since= --tail=
        https://kubernetes-v1-4.github.io/docs/user-guide/kubectl/kubectl_logs/

        prints the logs to stdout of program

        Returns:
            exit code
        """
        if experiment_name is None:
            experiment_name = self.current_experiment()
        pod_name, container_name = self.get_pod_container(experiment_name, process_name)
        return cmdline.run_raw(
            self._get_logs_cmd(
                pod_name, process_name, follow=follow,
                since=since, tail=tail, namespace=experiment_name
            ),
            print_cmd=False,
            dry_run=self.dry_run
        )

    def describe(self, process_name, experiment_name=None):
        if experiment_name is None:
            experiment_name = self.current_experiment()
        pod_name, container_name = self.get_pod_container(experiment_name, process_name)
        cmd = 'kubectl describe pod ' + pod_name + self._get_ns_cmd(experiment_name)
        return cmdline.run_verbose(cmd, print_out=True, 
                    raise_on_error=False, dry_run=self.dry_run)

    def print_logs(self, process_name,follow=False,since=0,tail=100,experiment_name=None):
        """
        kubectl logs <pod_name> <container_name>
        No error checking, no string caching, delegates to os.system
        """
        if experiment_name is None:
            experiment_name = self.current_experiment()
        pod_name, container_name = self.get_pod_container(experiment_name, process_name)
        cmd = self._get_logs_cmd(
            pod_name, container_name, follow=follow,
            since=since, tail=tail, namespace=namespace,dry_run=self.dry_run
        )
        cmdline.run_raw(cmd, dry_run=self.dry_run)

    # TODO: exec
    # TODO: ssh
    # TODO: Support surreal style for exec, ssh

    def exec(self, process_name, cmd, experiment_name=None):
        """
        kubectl exec -ti

        Args:
            component_name: can be agent-N, learner, ps, replay, tensorplex, tensorboard
            cmd: either a string command or a list of command args

        Returns:
            stdout string if is_print else None
        """
        if is_sequence(cmd):
            cmd = ' '.join(map(shlex.quote, cmd))
        if experiment_name is None:
            experiment_name = self.current_experiment()
        ns_cmd = self._get_ns_cmd(experiment_name)
        pod_name, container_name = self.get_pod_container(experiment_name, process_name)
        return cmdline.run_raw('kubectl exec -ti {} -c {} {} -- {}'.format(pod_name, 
                container_name, ns_cmd, cmd), dry_run=self.dry_run)

    def ssh(self, process_name, experiment_name=None):
        """
        kubectl exec -ti

        Args:
            TODO:

        Returns:
            TODO:
        """
        self.exec(process_name, 'bash', experiment_name)

    def _format_scp_path(self, f, experiment_name):
        if ':' in f:
            process_name, path = f.split(':')
            pod, container = self.get_pod_container(experiment_name, process_name)
            return process_name, '{}:{} -c {}'.format(pod, path, container)
        else:
            return None, f

    def scp(self, src_file, dest_file, experiment_name=None):
        """
        https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#cp
        kurreal cp /my/local/file learner:/remote/file mynamespace
        is the same as
        kubectl cp /my/local/file mynamespace/nonagent:/remote/file -c learner
        """
        if experiment_name is None:
            experiment_name = self.current_experiment()

        src_name, src_path = self._format_scp_path(src_file, experiment_name)
        dest_name, dest_path = self._format_scp_path(dest_file, experiment_name)
        assert (src_name is None) != (dest_name is None), \
            '[Error] one of "src_file" and "dest_file" must be remote and the other local.'
        cmd = 'kubectl cp {} {}'.format(src_path, dest_path)
        cmdline.run_raw(cmd, print_cmd=True, dry_run=self.dry_run)

    def gcloud_get_config(self, config_key):
        """
        Returns: value of the gcloud config
        https://cloud.google.com/sdk/gcloud/reference/config/get-value
        for more complex outputs, add --format="json" to gcloud command
        """
        out, _, _ = cmdline.run_verbose(
            'gcloud config get-value ' + config_key,
            print_out=False,
            raise_on_error=True,
            dry_run=self.dry_run
        )
        return out.strip()

    def gcloud_zone(self):
        """
        Returns: current gcloud zone
        """
        return self.gcloud_get_config('compute/zone')

    def gcloud_project(self):
        """
        Returns: current gcloud project
        https://cloud.google.com/sdk/gcloud/reference/config/get-value
        for more complex outputs, add --format="json" to gcloud command
        """
        return self.gcloud_get_config('project')

    def gcloud_configure_ssh(self):
        """
        Refresh the ssh settings for the current gcloud project
        populate SSH config files with Host entries from each instance
        https://cloud.google.com/sdk/gcloud/reference/compute/config-ssh
        """
        return cmdline.run_raw('gcloud compute config-ssh', dry_run=self.dry_run)

    def gcloud_url(self, node_name):
        """
        Returns: current gcloud project
        https://cloud.google.com/sdk/gcloud/reference/config/get-value
        for more complex outputs, add --format="json" to gcloud command
        """
        return '{}.{}.{}'.format(
            node_name, self.gcloud_zone(), self.gcloud_project()
        )

    def gcloud_ssh_node(self, node_name):
        """
        Don't forget to run gcloud_config_ssh() first
        """
        url = self.gcloud_url(node_name)
        return cmdline.run_raw(
            'ssh -o StrictHostKeyChecking=no ' + url,
            print_cmd=True, dry_run=self.dry_run,
        )