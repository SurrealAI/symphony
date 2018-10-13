# Kubernetes Guide
[Concepts](#concepts)
[Scheduling](#scheduling)
[Manaully Update Yaml](#manually-update-yaml)

You can use symphony as a templating engine for running tasks on kubernetes. All basic apis are supported. Kubernetes runs docker containers, so you will need to provide a container image for every process. 
```python
# Run experiment.py
from symphony.engine import Cluster
from symphony.kube import KubeCluster
cluster = Cluster.new('kubernetes') # cluster is a KubeCluster
exp = cluster.new_experiment('rl') # exp is a KubeExperimentSpec
learner = exp.new_process('learner', container_image='ubuntu:16,04', command='python', args=['learner.py'])
agent = exp.new_process('agent', container_image='ubuntu:16,04', command='python', args=['agent.py', '--env', 'half-cheetah']) # agent, learner are a KubeProcessSpec
learner.binds('replay-server')
learner.binds('parameter-server')
agent.connects('replay-server')
agent.connects('parameter-server')
learner.exposes('tensorboard')
cluster.launch(exp) # Runs agent.py and learner.py
```
Kubernetes uses yaml to specify each component to launch, our API closely reflects that. It is highly recommended that you go read the documentations on [kubernetes official website](https://kubernetes.io). 

# Concepts
In kubernetes a pod is a atomic unit of running application instance. Each process without a process group is mapped to a pod with one container. Each process group is mapped to a pod with one container per process. When you are using a process group, all pod-related functionalities should be called on a process group instead of a process. 

# Scheduling
One of the most important aspects of running tasks on Kubernetes is to schedule workloads to the correct machine. Symphony provides both lower-level Kubernetes based scheduling mechanisms for fine grained control and a higher-level interface when the Kubernetes cluster is created by [Cloudwise](https://github.com/SurrealAI/cloudwise).

* [Dispatcher (High Level Interface)](#dispatcher)

* [Resource Request](#resource-request)
* [Node Selector and Node Taint](#node-selector-and-node-taint)

## Dispatcher
`symphony.kube.GKEDispatcher` provides an abstract interface for scheduling. You can use it on clusters created by [Cloudwise](https://github.com/SurrealAI/cloudwise). After creating the cluster, you will obtain a `.tf.json` file. Provide the path to this file to the `GKEDispatcher` to configure the dispatcher instance. There are several scheduling options. For all these methods you need to provide the `symphony.kube.Process` and the `symphony.kube.ProcessGroup` containing this process (or `None` when the process does not belong to any process group).

* Assign to machine. Claim enough resources to occupy a single machine exclusively. Also supports fractions.
```python
# Occupies a machine in the CPU pool
dispatcher.assign_to_machine(process, node_pool_name='cpu-pool')
# Occupies 1/5 of a machine in the CPU pool
dispatcher.assign_to_machine(process, node_pool_name='cpu-pool', process_per_machine=5)
```
* Assign to GPU. Claim enough resources to occupy a single GPU. This is implemented by claiming a 1/n fraction of a n-GPU machine.
```python
# Occupies a GPU and claim other resources proportionally
dispatcher.assign_to_gpu(process, node_pool_name='gpu-pool')
# If every machine has 4 GPUs in gpu-pool, this is equivalent to
dispatcher.assign_to_machine(process, node_pool_name='gpu-pool', process_per_machine=4)
```
* Assign to resource. Claim specified resources on any applicable node pool in the cluster.
```python
dispatcher.assign_to_gpu(process, cpu=2.5, memory_m=4096, gpu_type='k80', gpu_count=2)
```
* Assign to node pool. Claim specified resources on a specified node pool.
```python
dispatcher.assign_to_node_pool(process, node_pool_name='gpu-pool-k80', cpu=2.5, memory_m=4096, gpu_count=2)
```
* Assign to \*. You can specify the mode in argument to the general `assign_to` function. This allows one to configure scheduling using config dictionaries.
```python
settings = {
    assign_to = 'machine',
    ...
}
dispatcher.assign_to(**settings)
```

## Resource request
Kubernetes has resource-request and resource-limit that allows one to request for cpu/memory/gpu. They are always configured on a process (container) level.
```python
proc.resource_request(cpu=1.5, mem='2G')
proc.resource_limit(cpu=1.5, mem='2G', gpu=1)  # gpu is mapped to nvidia.com/gpu
```

## Node selector and Node Taint
Kubernetes allows you to select which machine you want to deploy your process/process group on. There are two selecting mechanisms: selector and taint. Each node has its selector and taint. A pod can be scheduled on to a node if:
* For any node selector on the pod, the node satisfies it.
* For any taint on the node, the pod tolerates the taint.
```python
nonagent.node_selector(key='surreal-node', value='nonagent-cpu')
nonagent.add_toleration(key='surreal', operator='Exists', effect='NoExecute')
```
To look up selectors and taints, do 
```bash
gcloud config set container/use_v1_api false
gcloud beta containers node-pools describe nonagent-pool-cpu
```


# Manually Update Yaml
You can edit the yml directly by accessing:
```python
# If process does not belong to a process group
process.pod_yml
process.container_yml
# If process belongs to a process group
process_group.pod_yml
process.container_yml
```
