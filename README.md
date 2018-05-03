# Symphony: An orchestrating library that supports a variety of backends
# Index

# Installation

# Introduction
Symphony was developed initially to support [Surreal](https://github.com/SurrealAI/Surreal), a library for distributed reinforcement learning. We observe that there are certain features about distributed scientific computing that are shared and can be automated. (TODO: improve these features)
* More than one process is needed for an experiment. 
* The processes talk to each other through the network (host + pair).
* A project is usually developed locally first, but needs to be deployed to a cluster to do anything meaningful. 
* Making sure that every process is talking to the correct address takes a lot of boilerplate code that can be automated on a per-platform basis.
* Monitoring multiple experiments can be painful.
Symphony provides convenient functionalities for deploying such distributed tasks. Symphony provides a python interface for you to configure how an experiment should be run. Once the experiment is running, you can use the provided commandline utilities to monitor how an experiment is going.

# Processes, Experiments & Clusters
Symphony allows you to manage multiple experiments where each experiment contains processes that communicates with each other through network. How to run an experiment is declared by code and then launched on a `Cluster`, which is an abstraction for where you run the experiment. It can be a tmux server on your local machine or a remote Kubernetes cluster. Here is an example of a RL experiment. (# TODO: make sure that engine imports everything correctly, we don't want people to remember to import kube)
```python
# Run experiment.py
from symphony.engine import Cluster

cluster = Cluster.new('tmux') # cluster is a TmuxCluster
exp = cluster.new_experiment('rl') # exp is a TmuxExperimentSpec
learner = exp.new_process('learner', command='python', args=['learner.py'])
agent = exp.new_process('agent', command='python', args=['agent.py', '--env', 'half-cheetah']) # agent, learner are a TmuxProcessSpec

learner.binds('replay-server')
learner.binds('parameter-server')
agent.connects('replay-server')
agent.connects('parameter-server')

cluster.launch(exp) # Runs agent.py and learner.py in two tmux sessions
```
Here A `ProcessSpec` and `ExperimentSpec` contains all information of how to run each process. And a `Cluster` uses these information to get them running. 

For advanced usecases, there is also a notion of a "process group" which represents several closely related proceses. For those familiar with Kubernetes, a process group maps closely to a Pod with multiple containers. See ... for details (TODO:). 

TODO: configuring clusters. A physical cluster maps to a logical clusters. 

# Networking
Symphony automatically computes what ports and addresses are needed for each process and puts them into environment variables (`SYMPH_..._HOST`/`SYMPH_..._PORT`) for each of the process. So in `learner.py` you can do. 
```python
# learner.py
import os
...
replay_host = os.environ['SYMPH_REPLAY_SERVER_HOST']
replay_port = os.environ['SYMPH_REPLAY_SERVER_PORT']
server = ReplayServer(host=replay_host, port=replay_port)
...
```
And similarly you can connect to this address in agent. 
(TODO: provide communication primitives using zmq, as extension)

A process can declare networking in three ways: `bind`, `connect`, `expose`. 
* A process that `bind`s or `expose`s provides an endpoint. `process.bind('service')` or `process.bind(['service-1', 'service-2'])` tells symphony to assign a port to `service-1` (and `service-2`) and expose dns address and port so that other processes can connect to the binding process. One can also do `process.bind({'tensorboard': 6006})` where a specific port is assigned.
* `connect` to something (e.g. `service-1`) declares that the process expects some other process to `bind` to it. While the envorinment variables for the host/port will still be provided at run time (assuming that you did bind) even if you didn't call `connect`, it is recommended as connecting to some non-existent name will be caught and cause the program to fail during declaration, before the experiment even starts.
* `expose`


# Monitoring through commandline.
After you start running and experiment, symphony provides a convenient commandline interface to know how each of the processes are running. If you are using a process group and that process names are not unique, use `process_group/process` in place of `process`. 
* `symphony process` or `symphony p` lists the status of processes in an experiment.
```bash
$> symphony p
Group     Name         Ready  Restarts  State           
          agent-0      1      0         running: 23.2h  
          eval-0       1      0         running: 23.2h   
...
```
* `symphony logs <process_name>` retrieves logs from a given process. 
```bash
$> symphony logs agent-0
Agent starting ...
```
* `symphony list-experiments` (`symphony ls`) lists all running experiments.
```bash
$> symphony ls
experiment-0
experiment-1
...
```
* `symphony delete` (`symphony d`), `symphony delete-batch` (`symphony db`) terminates experiments.
* `symphony visit [exposed_service]` (`symphony vi`) opens a web browser to the exposed service (Use `--url-only` to only get the url).
* Other convenient functionalities can be used for some clusters, (e.g. Kubernetes). `exec, ssh, scp`.


