import json
import copy
from os.path import expanduser

_REQUIRED_LABELS = ["name", "cpu", "memory_m"]
_EFFECT_MAP = {
    'NO_EXECUTE': 'NoExecute',
    'NO_SCHEDULE': 'NoSchedule',
    'PREFER_NO_SCHEDULE': 'PreferNoSchedule'
}

# TODO: add env variable to limit program thread usage
class GKEDispatcher:
    def __init__(self, tf_json):
        """
        json is a dict or a str(in which case it is treated as a json file)
        """
        if not isinstance(tf_json, dict):
            with open(expanduser(str(tf_json)), 'r') as f:
                tf_json = json.load(f)
        self.tf_config = tf_json
        if "resource" not in self.tf_config or \
           "google_container_node_pool" not in self.tf_config["resource"]:
            raise KeyError("resource/google_container_node_pool is required in the json")
        self.node_pools = self.tf_config["resource"]["google_container_node_pool"]
        for k, v in self.node_pools.items():
            self._check_required_labels(k, v)

    def get_node_pools(self):
        """
        Returns a sorted list of all node_pools
        """
        return sorted(self.node_pools.keys())

    def get_node_pool(self, name):
        """
        Returns the terraform json entry of the node_pool with @name
        """
        if not name in self.node_pools:
            raise KeyError("Cannot find node pool {}, available:\n{}"
                           .format(name, ',\n'.join(self.get_node_pools())))
        return self.node_pools[name]

    def assign_to_node_pool(self,
                            process,
                            *,
                            node_pool_name,
                            process_group=None,
                            memory_m=None,
                            cpu=None,
                            gpu_count=None):
        """
        Assigns a symphony process to a machine on the specific node pool
        Args:
            process: symphony.process, container to claim resources
            node_pool_name: str, name of node pool to assign to
            process_group (default None): symphony.process_group,
                None implies that symphony.process is itself a pod
        """
        if process_group is None:
            process_group = process
        node_pool_di = self.get_node_pool(node_pool_name)

        np_labels = node_pool_di["node_config"]["labels"]
        name = np_labels["name"]

        # This selector selects the only node_pool
        process_group.node_selector("name", name)
        # Tolerations allow the process to be scheduled
        if "taint" in node_pool_di["node_config"]:
            for taint in node_pool_di["node_config"]["taint"]:
                taint = copy.copy(taint)
                if 'value' in taint:
                    taint['operator'] = 'Equal'
                if 'effect' in taint:
                    taint['effect'] = _EFFECT_MAP[taint['effect']]
                process_group.add_toleration(**taint)

        if memory_m is not None:
            memory_str = '{}Mi'.format(int(memory_m))
            process.resource_request(memory=memory_str)
        if cpu is not None:
            process.resource_request(cpu=cpu)
        if gpu_count is not None:
            process.resource_limit(gpu=gpu_count)

    def assign_to_machine(self,
                          process,
                          *,
                          node_pool_name,
                          process_group=None,
                          process_per_machine=1):
        node_pool_di = self.get_node_pool(node_pool_name)
        if process_group is None:
            process_group = process

        np_labels = node_pool_di["node_config"]["labels"]
        cpu = np_labels["cpu"]
        memory_m = np_labels["memory_m"]

        memory_share = memory_m / (process_per_machine + 1)
        cpu_share = (cpu - 0.6) / process_per_machine
        cpu_share = float(int(cpu_share * 1000)) / 1000

        if 'gpu_count' in np_labels:
            num_gpus = np_labels['gpu_count']
            gpu_share = max(int(num_gpus / process_per_machine), 1)
        else:
            gpu_share = None

        self.assign_to_node_pool(process,
                                 node_pool_name=node_pool_name,
                                 process_group=process_group,
                                 memory_m=memory_share,
                                 cpu=cpu_share,
                                 gpu_count=gpu_share)

    def assign_to_gpu(self,
                      process,
                      *,
                      node_pool_name,
                      process_group=None):
        node_pool_di = self.get_node_pool(node_pool_name)
        np_labels = node_pool_di["node_config"]["labels"]

        if 'gpu_count' not in np_labels:
            raise ValueError('Assigning by GPU on node_pool {} '
                             'that does not contain a gpu')
        num_gpus = np_labels['gpu_count']
        self.assign_to_machine(process,
                               node_pool_name=node_pool_name,
                               process_group=process_group,
                               process_per_machine=num_gpus)

    def assign_to_resource(self,
                           process,
                           *,
                           node_pool_name=None,
                           process_group=None,
                           memory_m=None,
                           cpu=None,
                           gpu_type=None,
                           gpu_count=None):
        """

        [description]

        Args:
            process: [description]
            *: [description]
            node_pool_name: [description] (default: {None})
            process_group: [description] (default: {None})
            memory_m: [description] (default: {None})
            cpu: [description] (default: {None})
            gpu_type: [description] (default: {None})
            gpu_count: [description] (default: {None})
        """
        if node_pool_name is None:
            node_pool_name = self.infer_node_pool_name(memory_m,
                                                       cpu,
                                                       gpu_type,
                                                       gpu_count)
        self.assign_to_node_pool(process,
                                 node_pool_name=node_pool_name,
                                 process_group=process_group,
                                 memory_m=memory_m,
                                 cpu=cpu,
                                 gpu_count=gpu_count)

    def infer_node_pool_name(self,
                             memory_m=None,
                             cpu=None,
                             gpu_type=None,
                             gpu_count=None):
        for node_pool_name, node_pool_di in self.node_pools.items():
            np_labels = node_pool_di["node_config"]["labels"]
            # TODO: add some margin to memory and cpu checks
            if memory_m is not None:
                memory_m_total = np_labels["memory_m"]
                if memory_m_total <= memory_m:
                    continue
            if cpu is not None:
                cpu_total = np_labels["cpu"]
                if cpu_total <= cpu:
                    continue
            if gpu_type is not None:
                if 'gpu_type' not in np_labels:
                    continue
                if gpu_type.lower() not in np_labels['gpu_type']:
                    continue
            if gpu_count is not None:
                if 'gpu_count' not in np_labels:
                    continue
                if gpu_count > np_labels['gpu_count']:
                    continue
            else:
                if 'gpu_count' in np_labels:
                    continue
            return node_pool_name
        raise ValueError('Cannot find nodepool to satisfy: ' +
                         'cpu={}, memory_m={}, '.format(cpu, memory_m) +
                         'gpu_type={}, and gpu_count={}'
                         .format(gpu_type, gpu_count))

    def assign_to(self,
                  process,
                  *,
                  assign_to,
                  **kwargs):
        to_delete = []
        for key, val in kwargs.items():
            if val is None:
                to_delete.append(key)
        for key_to_delete in to_delete:
            del kwargs[key_to_delete]
        if assign_to == 'node_pool':
            self.assign_to_node_pool(process, **kwargs)
        elif assign_to == 'machine':
            self.assign_to_machine(process, **kwargs)
        elif assign_to == 'gpu':
            self.assign_to_gpu(process, **kwargs)
        elif assign_to == 'resource':
            self.assign_to_resource(process, **kwargs)
        else:
            raise ValueError('assign_to_{} not supported. '.format(assign_to)
                             + 'Use node_pool, machine, gpu, or resource')

    def _check_required_labels(self, name, di):
        if "node_config" not in di:
            msg = "Missing field 'node_config' in declaration of node pool {}. ".format(name)\
                  + "Is this json generated by cloudwise?"
            raise ValueError(msg)
        if "labels" not in di["node_config"]:
            msg = "Missing field 'node_config/labels' in declaration of node pool {}. ".format(name)\
                  + "Is this json generated by cloudwise?"
            raise ValueError(msg)
        labels_di = di["node_config"]["labels"]
        for label in _REQUIRED_LABELS:
            if label not in labels_di:
                msg = "Missing field {} in labels for node_pool {}"\
                      .format(label, name)\
                      + "Is this json generated by cloudwise?"
                raise ValueError(msg)

    def __repr__(self):
        return "{}, available node_pools:\n".format(str(type(self)))\
                + ',\n'.join(self.get_node_pools())


class GKEMachineDispatcher:
    def __init__(self, tf_json):
        """
        json is a dict or a str(in which case it is treated as a json file)
        """
        if not isinstance(tf_json, dict):
            with open(str(tf_json), 'r') as f:
                tf_json = json.load(f)
        self.tf_config = tf_json
        if "resource" not in self.tf_config or \
           "google_container_node_pool" not in self.tf_config["resource"]:
            raise KeyError("resource/google_container_node_pool is required in the json")
        self.node_pools = self.tf_config["resource"]["google_container_node_pool"]
        for k, v in self.node_pools.items():
            self._check_required_labels(k, v)

    def get_node_pools(self):
        """
        Returns a sorted list of all node_pools
        """
        return sorted(self.node_pools.keys())

    def get_node_pool(self, name):
        """
        Returns the terraform json entry of the node_pool with @name
        """
        if not name in self.node_pools:
            raise KeyError("Cannot find node pool {}, available:\n{}"
                           .format(name, ',\n'.join(self.get_node_pools())))
        return self.node_pools[name]

    def assign_to_nodepool(self,
                           process,
                           node_pool_name,
                           *,
                           process_group=None,
                           exclusive=True):
        """
        Assigns a symphony process to a machine on the specific node pool
        Args:
            exclusive: When true, claim all available resoruces on this node
                On gpu machines, claim resources for one gpu when
                applicable
        """
        if not node_pool_name in self.node_pools:
            raise KeyError("Cannot find node pool {}".format(node_pool_name))
        if process_group is None:
            process_group = process
        node_pool_di = self.node_pools[node_pool_name]

        np_labels = node_pool_di["node_config"]["labels"]
        name = np_labels["name"]
        cpu = np_labels["cpu"]
        memory_m = np_labels["memory_m"]

        # This selector selects the only node_pool
        process_group.node_selector("name", name)
        # Tolerations allow the process to be scheduled
        if "taint" in node_pool_di["node_config"]:
            for taint in node_pool_di["node_config"]["taint"]:
                taint = copy.copy(taint)
                if 'value' in taint:
                    taint['operator'] = 'Equal'
                if 'effect' in taint:
                    taint['effect'] = _EFFECT_MAP[taint['effect']]
                process_group.add_toleration(**taint)
        if "gpu_type" in np_labels:
            process_group.add_toleration(**{
                "effect": "NoSchedule",
                "key": "nvidia.com/gpu",
                "operator": "Exists"
                })
        if exclusive:
            # Exclusive by GPUS
            if 'gpu_count' in np_labels:
                num_gpus = np_labels['gpu_count']
            else:
                num_gpus = 1

            memory_str = '{}Mi'.format(int(memory_m / (num_gpus + 1)))
            cpu_share = (cpu - 0.6) / num_gpus
            cpu_share = float(int(cpu_share * 1000)) / 1000
            process.resource_request(cpu=cpu_share, memory=memory_str)
            if "gpu_count" in np_labels:
                process.resource_limit(gpu=1)

    def _check_required_labels(self, name, di):
        if "node_config" not in di:
            msg = "Missing field 'node_config' in declaration of node_pool {}. ".format(name)\
                  + "Is this json generated by cloudwise?"
            raise ValueError(msg)
        if "labels" not in di["node_config"]:
            msg = "Missing field 'node_config/labels' in declaration of node_pool {}. ".format(name)\
                  + "Is this json generated by cloudwise?"
            raise ValueError(msg)
        labels_di = di["node_config"]["labels"]
        for label in _REQUIRED_LABELS:
            if label not in labels_di:
                msg = "Missing field {} in labels for node_pool {}".format(label, name)\
                      + "Is this json generated by cloudwise?"
                raise ValueError(msg)

    def __repr__(self):
        return "{}, available node_pools:\n".format(str(type(self)))\
                + ',\n'.join(self.get_node_pools())
