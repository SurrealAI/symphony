"""
Top-down construction of the launch spec
Order of spec: Cluster -> Experiment -> ProcessGroup -> Process
"""
from symphony.engine import *
from symphony.kube import *


def test_kube_topdown():
    cluster = Cluster.new('kube')
    exp = cluster.new_experiment('exp')
    nonagent = exp.new_process_group('group')
    learner = nonagent.new_process('proc1', container_image='def', command='cmd1')
    learner.binds('myserver')
    replay = nonagent.new_process('proc2',  container_image='cpu', args='cmd2')
    replay.connects('myserver')

    agents = []
    for i in range(8):
        agent = exp.new_process('agent' + str(i), container_image='gpu', args=['--cmd'])
        agent.connects('myserver')
        agents.append(agent)

    tb = exp.new_process('tb', container_image='tensorboard', args=['--logdir'])
    tb.exposes('tensorboard')

    # do some more kube specific things
    for process in exp.list_processes():
        process.mount_nfs(server='surreal-shared-fs-vm', path='/data', mount_path='/fs')

    tb.resource_request(cpu=1.7)
    tb.node_selector(key='surreal-node', value='agent')
    tb.add_toleration(key='surreal', operator='Exists', effect='NoExecute')
    tb.image_pull_policy('Always')

    # nonagent.resource_request(cpu=7) This is not well defined, do we want every container 
    # to request for 7 cpus? Or do we want the first container to request for 7 cpus?
    learner.resource_request(cpu=7)
    nonagent.node_selector(key='surreal-node', value='nonagent-cpu')
    nonagent.add_toleration(key='surreal', operator='Exists', effect='NoExecute')

    nonagent.image_pull_policy('Always')

    cluster.launch(exp, dry_run=True)
