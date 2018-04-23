"""
Bottom-up construction of the launch spec
Order of spec: Process -> ProcessGroup -> Experiment -> Cluster
"""
from symphony.engine import *
from symphony.kube import *


learner = KubeProcessSpec('proc1', 'cmd1')
learner.binds('myserver')
replay = KubeProcessSpec('proc2', 'cmd2')
replay.connects('myserver')

nonagent = KubeProcessGroupSpec('group', 'args')
nonagent.add_processes([learner, replay])
# kube specific
nonagent.resource_request(cpu=7)
nonagent.node_selector(key='surreal-node', value='nonagent-cpu')
nonagent.add_toleration(key='surreal', operator='Exists', effect='NoExecute')
nonagent.image_pull_policy('Always')

agents = []
for i in range(8):
    agent = KubeProcessSpec('agent' + str(i), '--cmd')
    agent.connects('myserver')
    agents.append(agent)

tb = KubeProcessSpec('tb', '--logdir')
tb.exposes('tensorboard')
# kube specific
tb.resource_request(cpu=1.7)
tb.node_selector(key='surreal-node', value='agent')
tb.add_toleration(key='surreal', operator='Exists', effect='NoExecute')
tb.image_pull_policy('Always')

exp = KubeExperimentSpec('exp', 'args', 'arg2')
exp.add_process_group(nonagent)
exp.add_processes(agents)
exp.add_process(tb)

# do some more kube specific things
for process in exp.all_processes():
    process.mount_nfs(server='surreal-shared-fs-vm', path='/data', mount_path='/fs')

cluster = Cluster.use('kube')
cluster.launch(exp)
