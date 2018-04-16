from symphony.cluster.kubecluster import KubeCluster, KubeNFSVolume, KubeGitVolume
from symphony.experiment import ProcessConfig, ProcessGroupConfig, ExperimentConfig

# These methods are initializing processes and their relations. 
# We organize things in two layers: Experiment contains multiple processes.
# There can an additional layer of structure called process group, 
# which wraps around processes.
# See experiment/*.py
# 
# Here we are declaring these experiment/process groups/processes
learner = ProcessConfig('learner', container_image='us.gcr.io/surreal-dev-188523/surreal-cpu:latest', args=['--cmd', 'echo "abc"; sleep 1000'])
# This means we assign a host/port to this process 
# and any process requesting parameter-sever can know how to connect to it
learner.provides('parameter-server') 
# I can call learner.provides(parameter_server=6006) instead to provide service at a specific port 
# TODO: fix the naming issue, cannot do "parameter-server=6006" in python
learner.requests('samples')
# This means exposing the port to external 
learner.exposes('tensorboard') 
# I can call learner.exposes(tensorboard=6006) instead to expose a specific port 
# This means reserving a port 
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

# Above are backend-independent data. The goal is that we can run an experiment 
# on any backend (though maybe very inefficiently)

# Below we declare a specific (the only we support right now) backend 
c = KubeCluster()

# Use kube-specific configs
exp.use_kube()

# Below we are defining how the experiment should be run on the kube cluster
# 
# Kubernetes accepts a yml describing on all the pods 
# (corresponding to a process group or a process without a process group) 
# Inspect [process/process group].kube.data to see the jsons.
# All the methods called below are convenience methods for manipulating json
# See cluster_config/kubernetes.py
# 
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