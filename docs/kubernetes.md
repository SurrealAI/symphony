# Kubernetes Guide
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

# Note
In kubernetes a pod is a atomic unit of running application instance. Each process without a process group is mapped to a pod with one container. Each process group is mapped to a pod with one container per process. When you are using a process group, all pod-related functionalities should be called on a process group instead of a process. 

# Resource request
Kubernetes has resource-request and resource-limit that allows one to request for cpu/memory/gpu. They are always configured on a process level.
```python
proc.resource_request(cpu=1.5, mem='2G')
proc.resource_limit(cpu=1.5, mem='2G', gpu=1) # gpu is mapped to nvidia.com/gpu
```

# Node selector
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
(!! Internal only) Currently our node pools are configured as follows
* n1-standard-2  
Labels: surreal-node : agent  
Taints: NO_EXECUTE surreal=true  
* n1-highmem-8  
Labels: surreal-node : nonagent-cpu  
Taints: NO_EXECUTE surreal=true  
* n1-highmem-8 1 k80  
Labels: surreal-node : nonagent-gpu  
Taints: gpu_taint, automatically added when a pod requests gpu
* n1-standard-16 1 p100  
Labels: surreal-node :  n1-standard-16-1p100  
Taints: gpu_taint, automatically added when a pod requests gpu
* n1-standard-16 1 p100  
Labels: surreal-node : nonagent-gpu-2k80-16cpu  
Taints: gpu_taint, automatically added when a pod requests gpu


# Manual update
You can edit the yml directly by accessing:
```python
# If process does not belong to a process group
process.pod_yml
process.container_yml
# If process belongs to a process group
process_group.pod_yml
process.container_yml
```

