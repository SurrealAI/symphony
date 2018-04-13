from symphony.cluster.kubecluster import KubeCluster, KubeNFSVolume, KubeGitVolume
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
nonagent.add_process(learner, replay)

exp = ExperimentConfig('Surreal Example')
exp.add_process_group(nonagent)
exp.add_process(agent)

# Use kube-specific configs
exp.use_kube()

# Mount volumes
nfs_volume = KubeNFSVolume(name='fs', server='surrealfs', path='/data')
surreal_volume = KubeGitVolume(name='repo_surreal', repository='https://github.com/surrealAI/surreal', revision='snapshot') # revision can be commit / 
for process in exp.processes.values():
    process.kube.mount_volume(nfs_volume, '/fs')
    process.kube.mount_volume(surreal_volume, '/mylib/surreal')

agent.kube.resource_request(cpu=1.7)
agent.kube.node_selector(key='surreal-node', value='agent')
agent.kube.add_toleration(key='surreal', operator='Exists', effect='NoExecute')
agent.kube.image_pull_policy('Always')

learner.kube.resource_request(cpu=7.7)
learner.kube.resource_limit(gpu=1)
nonagent.kube.node_selector(key='surreal-node', value='nonagent')
nonagent.kube.add_toleration(key='surreal', operator='Exists', effect='NoExecute')
nonagent.kube.image_pull_policy('Always')

c.launch(exp)
c.pod('kube-system')