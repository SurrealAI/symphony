"""
Top-down construction of the launch spec
Order of spec: Cluster -> Experiment -> ProcessGroup -> Process
"""
from symphony.engine import *
from symphony.kube import *
import json
import unittest

class SerializationTest:
    """docstring for SerializationTest"""
    
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


    di = exp.dump_dict()

    # str_1 = json.dumps(exp.compile())

    # print(di)

    experiment = KubeExperimentSpec.load_dict(di)
    # print(experiment)
    # 
    def test_addressbook(self):
        e1 = self.exp
        assert exp.ab.entries == di['ab']

    def test_correct(self):
        self.maxDiff = None
        e1 = self.exp._compile()
        e2 = self.experiment._compile()
        assert e1 == e2

if __name__ == '__main__':
    unittest.main()