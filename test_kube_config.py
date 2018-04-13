from symphony.cluster.kubecluster import KubeCluster
from symphony.experiment import ProcessConfig, ProcessGroupConfig, ExperimentConfig

c = KubeCluster()

learner = ProcessConfig('learner', container_image='surreal-cpu', args=['echo', 'vcafkdla'])
learner.provides('parameter-server')
learner.requests('samples')
learner.exposes('tensorboard')
learner.reserves(load_balancing=7002)
replay = ProcessConfig('replay', container_image='surreal-cpu', args=['echo', 'def'])
replay.provides('samples')
agent = ProcessConfig('agent-0', container_image='surreal-cpu', args=['echo', 'ahc'])
agent.requests('parameter-server')
nonagent = ProcessGroupConfig('Nonagent')
exp = ExperimentConfig('Surreal Example')
nonagent.add_process(learner, replay)
exp.add_process_group(nonagent)
exp.add_process(agent)


c.launch(exp)