# Symphony: An orchestrating library that supports a variety of backends
Symphony aims to ease the process of launching and monitoring multi-process / multi-node computation tasks. It provides a simple abstraction for launching multiple processes in a centralized place and supports multiple backends (e.g. tmux and kubernetes). It also provides a set of essential commandline interfaces to monitor the status of the processes involved.

# Index

# Installation

# Motivation
Symphony was developed initially to support [Surreal](https://github.com/SurrealAI/Surreal), a library for distributed reinforcement learning. We observe that there are certain features about distributed scientific computing that are shared and can be automated.
* More than one process is needed for an experiment. 
* The processes talk to each other through the network (host + port).
* A project is usually developed locally first, but needs to be deployed to a cluster to do anything meaningful. 
* Making sure that every process is talking to the correct address takes a lot of boilerplate code that can be automated on a per-platform basis.
* Monitoring multiple experiments can be painful. Code written for this purpose is mostly project agnostic.
Symphony provides convenient functionalities for deploying such distributed tasks. You configure how an experiment should be run and then kick it off in a python interface. Once the experiment is running, you can use (and/or extend) the provided commandline utilities to monitor how an experiment is going.

# Processes, Experiments & Clusters
Symphony allows you to manage multiple experiments where each experiment contains processes that communicates with each other through network. How to run an experiment is declared by code and then launched on a `Cluster`, which is an abstraction for where you run the experiment. It can be a tmux server on your local machine or a remote Kubernetes cluster. Here is an example of a RL experiment. (# TODO: make sure that engine imports everything correctly, we don't want people to remember to import kube)
```python(TODO: update to reflect the latest tmux api)
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
* `process.bind('service')` tells symphony to assign a port to `service-1` and expose both DNS address and port so that other processes can connect to the binding process. All pocesses will have access to environment variables `SYMPH_SERVICE_1_HOST` and `SYMPH_SERVICE_1_PORT`. One can also do `process.bind({'tensorboard': 6006})` where a specific port is assigned. 
* `connect` to something (e.g. `service-1`) declares that the process expects some other process to `bind` to it. While the envorinment variables for the host/port will still be provided at run time (assuming that you did bind) even if you didn't call `connect`, it is recommended as connecting to some non-existent name will be caught and cause the program to fail during declaration, before the experiment even starts.
* `expose` is used when you are running experiments on a cloud. It tells symphony to expose this port to a global ip. If you have a process expose `tensorboard` you can later use `symphony visit tensorboard` to retrieve an ip and open a browser for it. There will also be environment variables `SYMPH_TENSORBOARD_HOST` and `SYMPH_TENSORBOARD_PORT`.

# Monitoring through commandline.
After you start running and experiment, symphony provides a convenient commandline interface to know how each of the processes are running. The script installed with symphony is mainly used for demonstration and prototyping. For your own project, you can merge the interface with your python script easily. See #[this example](using-symphony-as-part-of-your-project).

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
* Other convenient functionalities can be used for some clusters, (e.g. Kubernetes). `exec, ssh, scp`. (TODO: document them)
* If you are using a process group and that process names are not unique, use `process_group/process` in place of `process`. 

# Config
Symphony provides several optional functionalities to help organize experiments. They are controlled by `SymphonyConfig` singleton. 
```python
from symphony.engine import SymphonyConfig
```
* `set_username(name)` makes all subsequently created experiments prepend username
```python
SymphonyConfig().set_username('sarah')
cluster = Cluster.new('tmux') # cluster is a TmuxCluster
exp1 = cluster.new_experiment('rl') # exp is a TmuxExperimentSpec
print(exp1.name) # 'sarah-rl' 
```
* `set_experiment_folder(directory)` saves all subsequently launched experiment specs to `directory`. You can retrieve your declaration of experiments later. It also allows the cluster to complain to you if you are going to overwrite an existing experiment. (You can still pass 'force=True' to force overwrite)
```python
SymphonyConfig().set_experiment_folder('~/foo')
cluster = Cluster.new('tmux') # cluster is a TmuxCluster
exp1 = cluster.new_experiment('rl') # exp is a TmuxExperimentSpec
cluster.launch(exp1) 
# information about this experiment will be saved to ~/foo/rl
```

# Using symphony as part of your project
To use symphony for your own project, the easiest way is to extend the provided parser. You only need to do three things in a class that extends `SymphonyParser`:
1. Overwrite `create_cluster(self)`, define the backend that you want to use
2. Overwrite `setup(self)`, add a new subcommand for launch (so you can launch things) and (optionally) set configs 
3. Declare your experiment and launch it. (Here we show how to add it as another subcommand of the script.)
(TODO: clean up the imports)
```python
# myproject.py
from symphony.commandline import SymphonyParser
from symphony.engine import Cluster
from symphony.kube import KubeCluster
import sys

class MyProjectParser(SymphonyParser):
    def create_cluster(self): # step 1
        return Cluster.new('kube')

    def setup(self): # step 2
        super().setup()
        SymphonyConfig().set_username('sarah')
        parser = self.add_subparser('create') 
        # add subcommand: `python myproject.py create`
        # This subcommand is mapped to self.action_create(args)
        parser.add_argument(...)

    def action_create(self, args): # step 3
        exp = self.cluster.new_experiment('foo')
        p = exp.new_process(...)
        ...
        self.cluster.launch(exp)

if __name__ == '__main__':
MyProjectParser().main()
```
Now not only can you do `python myproject.py create` to launch an experiment, but you can also use `python myproject.py process` to monitor the processes of your experiment. 




