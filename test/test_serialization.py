"""
Top-down construction of the launch spec
Order of spec: Cluster -> Experiment -> ProcessGroup -> Process
"""
from symphony.engine import *
from symphony.kube import *
import json
import unittest

class TestSerialization:
    """docstring for SerializationTest"""
    def prep_env(self):
        exp = KubeExperimentSpec('exp')
        nonagent = exp.new_process_group('group')
        learner = nonagent.new_process('proc1')
        learner.binds('myserver')
        replay = nonagent.new_process('proc2')
        replay.connects('myserver')

        agents = []
        for i in range(8):
            agent = exp.new_process('agent' + str(i))
            agent.connects('myserver')
            agents.append(agent)

        tb = exp.new_process('tb')
        tb.exposes('tensorboard')

        for process in exp.list_processes():
            process.mount_nfs(server='surreal-shared-fs-vm', path='/data', mount_path='/fs')

        tb.resource_request(cpu=1.7)
        tb.node_selector(key='surreal-node', value='agent')
        tb.add_toleration(key='surreal', operator='Exists', effect='NoExecute')
        tb.image_pull_policy('Always')

        learner.resource_request(cpu=7)
        nonagent.node_selector(key='surreal-node', value='nonagent-cpu')
        nonagent.add_toleration(key='surreal', operator='Exists', effect='NoExecute')

        return exp
    
    def test_addressbook(self):
        exp = self.prep_env()
        di = exp.dump_dict()
        assert exp.address_book.entries == di['ab']

    def test_correct(self):
        exp = self.prep_env()
        di = exp.dump_dict()
        experiment = KubeExperimentSpec.load_dict(di)
        e1 = exp._compile()
        e2 = experiment._compile()
        assert e1 == e2
