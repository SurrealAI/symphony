# User Guide for Tmux Backend
For jobs running locally in background (e.g. to test new changes),
Symphony can use `tmux` to launch and manage them. 

```python
from symphony.engine import Cluster

# Create a Cluster with tmux as the backend
cluster = Cluster.new('tmux') # cluster is a TmuxCluster

# Create an Experiment spec to run on this cluster.
exp = cluster.new_experiment('hello-world')

server = exp.new_process('server', cmds=['source activate symphony', 'python run_simple_client.py'])
client = exp.new_process('client', cmds=['source activate symphony', 'python run_simple_server.py'])
server.binds('example')
client.connects('example')
cluster.launch(exp)

print('Server and client are running in a tmux session')
print('Run "tmux ls" to see your processes')
```

## Abstractions
Symphony uses the following abstractions:
* Experiment <---> tmux session
* Process <---> tmux window

By default, each tmux window has the same name as the process running inside.
However, if the process is part of a process group
(logical grouping of related processes), then the name is prefixed by
`process_group_name:`

## Tmux Details
In order to avoid interfering with the user's tmux session,
Symphony by default runs all its experiments in a new tmux _server_
named `__symphony__`.
Thus, to check the status of running jobs, you can simply attach
to the tmux session by running:
```bash
tmux -L __symphony__ attach -t session_name
```

You can specify a custom tmux server name if desired when creating the cluster:
```python
cluster = Cluster.new('tmux', server_name='custom_server')
# Create experiments, etc.
```
