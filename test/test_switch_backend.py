"""
Top-down construction of the launch spec
Order of spec: Cluster -> Experiment -> ProcessGroup -> Process
"""
from symphony.engine import *
from symphony.kube import *


def create_common_spec(backend):
    cluster = Cluster.new(backend)
    exp = cluster.new_experiment('exp', 'args', 'arg2')
    nonagent = exp.new_process_group('group', 'args')
    learner = nonagent.new_process('proc1', 'cmd1')
    learner.binds('myserver')
    replay = nonagent.new_process('proc2', 'cmd2')
    replay.connects('myserver')

    agents = []
    for i in range(8):
        agent = exp.new_process('agent' + str(i), '--cmd')
        agent.connects('myserver')
        agents.append(agent)

    tb = exp.new_process('tb', '--logdir')
    tb.exposes('tensorboard')
    return cluster, exp


def create_tmux_cluster():
    cluster, exp = create_common_spec('tmux')
    # add tmux specific things


def create_kube_cluster():
    cluster, exp = create_common_spec('kube')
    # add kube specific things
    for process in exp.all_processes():
        process.mount_nfs(server='surreal-shared-fs-vm', path='/data', mount_path='/fs')

    tb = exp.get_process('tb')
    tb.resource_request(cpu=1.7)
    tb.node_selector(key='surreal-node', value='agent')
    tb.add_toleration(key='surreal', operator='Exists', effect='NoExecute')
    tb.image_pull_policy('Always')

    nonagent = exp.get_process_group('nonagent')
    nonagent.resource_request(cpu=7)
    nonagent.node_selector(key='surreal-node', value='nonagent-cpu')
    nonagent.add_toleration(key='surreal', operator='Exists', effect='NoExecute')

    nonagent.image_pull_policy('Always')

    cluster.launch()
