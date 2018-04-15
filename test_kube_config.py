from symphony.cluster.kubecluster import KubeCluster, KubeNFSVolume, KubeGitVolume
from symphony.experiment import ProcessConfig, ProcessGroupConfig, ExperimentConfig

c = KubeCluster()

learner = ProcessConfig('learner', container_image='us.gcr.io/surreal-dev-188523/surreal-cpu:latest', args=['--cmd', 'echo "abc"; sleep 1000'])
learner.provides('parameter-server')
learner.requests('samples')
learner.exposes('tensorboard')
learner.reserves(load_balancing=7002)

replay = ProcessConfig('replay', container_image='us.gcr.io/surreal-dev-188523/surreal-cpu:latest', args=['--cmd', 'echo "abc"; sleep 1000'])
replay.provides('samples')

agent = ProcessConfig('agent-0', container_image='us.gcr.io/surreal-dev-188523/surreal-cpu:latest', args=['--cmd', 'echo "abc"; sleep 1000'])
agent.requests('parameter-server')

nonagent = ProcessGroupConfig('Nonagent')
nonagent.add_process(learner, replay)

exp = ExperimentConfig('Symphony-test-1')
exp.add_process_group(nonagent)
exp.add_process(agent)

# Use kube-specific configs
exp.use_kube()

# Mount volumes
# nfs_volume = KubeNFSVolume(name='fs', server='surreal-shared-fs-vm', path='/data')
# surreal_volume = KubeGitVolume(name='repo_surreal', repository='https://github.com/surrealAI/surreal', revision='snapshot') # revision can be commit / 
for process in exp.processes.values():
    process.kube.mount_nfs(server='surreal-shared-fs-vm', path='/data', mount_path='/fs')
    # v = process.kube.mount_git_repo(repository='https://github.com/surrealAI/surreal', revision='snapshot', mount_path='/mylib/surreal')

agent.kube.resource_request(cpu=1.7)
agent.kube.node_selector(key='surreal-node', value='agent')
agent.kube.add_toleration(key='surreal', operator='Exists', effect='NoExecute')
agent.kube.image_pull_policy('Always')

learner.kube.resource_request(cpu=7)
# learner.kube.resource_limit(gpu=0)
nonagent.kube.node_selector(key='surreal-node', value='nonagent-cpu')
nonagent.kube.add_toleration(key='surreal', operator='Exists', effect='NoExecute')
nonagent.kube.image_pull_policy('Always')

c.launch(exp)
# c.pod('kube-system')