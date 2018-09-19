# Internal ONLY

- Caraml is our protocol library, which includes useful primitives that hide the user from those gory ZMQ socket details. The classes you will use are (`ZmqClient`, `ZmqServer`) pair, (`ZmqPush`, `ZmqPull`) pair, (`ZmqPub`, `ZmqSub`) pair in `caraml.zmq.communicator`. The best tutorial with code is in `caraml/test/test_communicator.py`, which shows you how each primitive works in the most minimal setup. 

- To run caraml on Kube, you will need Symphony's kube mode. Run the example in `symphony/examples/zmq`. It is a complete example from docker image building to deploying on kube. 

- The kube example above only shows a fraction of symphony's features. For real-life example, please refer to the `create_surreal()` function in `surreal/kube/kurreal.py`, which configures the full-fledged Surreal distributed algorithm. It makes use of features like mounting NFS, setting hardware resources, adding node-selectors and node-taints, etc. For your convenience, the code snippet is copied and pasted below:


```python
from symphony.commandline import SymphonyParser
from symphony.engine import SymphonyConfig, Cluster
from symphony.addons import DockerBuilder, clean_images

C = config  # config dictionary
cluster = Cluster.new('kube')
exp = cluster.new_experiment(experiment_name)

# Read pod specifications
assert agent_pod_type in C.pod_types, \
    'agent pod type not found in `pod_types` section in ~/.surreal.yml'
assert nonagent_pod_type in C.pod_types, \
    'nonagent pod type not found in `pod_types` section in ~/.surreal.yml'
if eval_pod_type is None: eval_pod_type = agent_pod_type
assert eval_pod_type in C.pod_types, \
    'eval pod type not found in `pod_types` section in ~/.surreal.yml'

agent_pod_spec = copy(C.pod_types[agent_pod_type])
nonagent_pod_spec = copy(C.pod_types[nonagent_pod_type])
eval_pod_spec = copy(C.pod_types[eval_pod_type])

agent_resource_request = agent_pod_spec.get('resource_request', {})
nonagent_resource_request = nonagent_pod_spec.get('resource_request', {})
eval_resource_request = eval_pod_spec.get('resource_request', {})

agent_resource_limit = agent_pod_spec.get('resource_limit', {})
nonagent_resource_limit = nonagent_pod_spec.get('resource_limit', {})
eval_resource_limit = eval_pod_spec.get('resource_limit', {})

images_to_build = {}
# defer to build last, so we don't build unless everythingpasses
if 'build_image' in agent_pod_spec:
    image_name = agent_pod_spec['build_image']
    images_to_build[image_name] = agent_pod_spec['image']
    # Use experiment_name as tag
    agent_pod_spec['image'] = '{}:{}'.format(agent_pod_spec['image'], exp.name)
if 'build_image' in nonagent_pod_spec:
    image_name = nonagent_pod_spec['build_image']
    images_to_build[image_name] = nonagent_pod_spec['image']
    nonagent_pod_spec['image'] = '{}:{}'.format(nonagent_pod_spec['image'], exp.name)
if has_eval:
    if 'build_image' in eval_pod_spec:
        image_name = eval_pod_spec['build_image']
        images_to_build[image_name] = eval_pod_spec['image']
        eval_pod_spec['image'] = '{}:{}'.format(eval_pod_spec['image'], exp.name)

nonagent = exp.new_process_group('nonagent')
learner = nonagent.new_process('learner', container_image=nonagent_pod_spec.image, args=[cmd_dict['learner']])
replay = nonagent.new_process('replay', container_image=nonagent_pod_spec.image, args=[cmd_dict['replay']])
ps = nonagent.new_process('ps', container_image=nonagent_pod_spec.image, args=[cmd_dict['ps']])
tensorboard = nonagent.new_process('tensorboard', container_image=nonagent_pod_spec.image, args=[cmd_dict['tensorboard']])
tensorplex = nonagent.new_process('tensorplex', container_image=nonagent_pod_spec.image, args=[cmd_dict['tensorplex']])
loggerplex = nonagent.new_process('loggerplex', container_image=nonagent_pod_spec.image, args=[cmd_dict['loggerplex']])

agents = []
agent_pods = []
if colocate_agent > 1:
    assert len(cmd_dict['agent']) % colocate_agent == 0
    for i in range(int(len(cmd_dict['agent']) / colocate_agent)):
        agent_pods.append(exp.new_process_group('agent-pg-{}'.format(i)))
    for i, arg in enumerate(cmd_dict['agent']):
        pg_index = int(i / colocate_agent)
        agent_p = agent_pods[pg_index].new_process('agent-{}'.format(i), container_image=agent_pod_spec.image, args=[arg])
        agents.append(agent_p)
elif batch_agent > 1:
    for i, arg in enumerate(cmd_dict['agent-batch']):
        agent_p = exp.new_process('agents-{}'.format(i), container_image=agent_pod_spec.image, args=[arg])
        agent_pods.append(agent_p)
        agents.append(agent_p)
else:
    for i, arg in enumerate(cmd_dict['agent']):
        agent_p = exp.new_process('agent-{}'.format(i), container_image=agent_pod_spec.image, args=[arg])
        agent_pods.append(agent_p)
        agents.append(agent_p)
evals = []
if has_eval:
    if batch_agent > 1:
        for i, arg in enumerate(cmd_dict['eval-batch']):
            eval_p = exp.new_process('evals-{}'.format(i), container_image=eval_pod_spec.image, args=[arg])
            evals.append(eval_p)
    else:
        for i, arg in enumerate(cmd_dict['eval']):
            eval_p = exp.new_process('eval-{}'.format(i), container_image=eval_pod_spec.image, args=[arg])
            evals.append(eval_p)

for proc in itertools.chain(agents, evals):
    proc.connects('ps-frontend')
    proc.connects('collector-frontend')

ps.binds('ps-frontend')
ps.binds('ps-backend')
ps.connects('parameter-publish')

replay.binds('collector-frontend')
replay.binds('sampler-frontend')
replay.binds('collector-backend')
replay.binds('sampler-backend')

learner.connects('sampler-frontend')
learner.binds('parameter-publish')
learner.binds('prefetch-queue')

tensorplex.binds('tensorplex')
loggerplex.binds('loggerplex')

for proc in itertools.chain(agents, evals, [ps, replay, learner]):
    proc.connects('tensorplex')
    proc.connects('loggerplex')

tensorboard.exposes({'tensorboard': 6006})

if not C.fs.type.lower() in ['nfs']:
    raise NotImplementedError('Unsupported file server type: "{}". '
                              'Supported options are [nfs]'.format(C.fs.type))
nfs_server = C.fs.server
nfs_server_path = C.fs.path_on_server
nfs_mount_path = C.fs.mount_path

for proc in exp.list_all_processes():
    # Mount nfs
    proc.mount_nfs(server=nfs_server, path=nfs_server_path, mount_path=nfs_mount_path)

resource_limit_gpu(agent_resource_limit)
agent_selector = agent_pod_spec.get('selector', {})
for proc in agents:
    # required services
    proc.resource_request(**agent_resource_request)
    proc.resource_limit(**agent_resource_limit)
    proc.image_pull_policy('Always')

for proc_g in agent_pods:
    proc_g.add_toleration(key='surreal', operator='Exists', effect='NoExecute')
    proc_g.restart_policy('Never')
    for k, v in agent_selector.items():
        proc_g.node_selector(key=k, value=v)

resource_limit_gpu(eval_resource_limit)
eval_selector = eval_pod_spec.get('selector', {})
for eval_p in evals:
    eval_p.resource_request(**eval_resource_request)
    eval_p.resource_limit(**eval_resource_limit)
    eval_p.image_pull_policy('Always')
    eval_p.add_toleration(key='surreal', operator='Exists', effect='NoExecute')
    eval_p.restart_policy('Never')
    for k, v in eval_selector.items():
        eval_p.node_selector(key=k, value=v)

learner.set_env('DISABLE_MUJOCO_RENDERING', "1")
learner.resource_request(**nonagent_resource_request)

resource_limit_gpu(nonagent_resource_limit)
learner.resource_limit(**nonagent_resource_limit)

non_agent_selector = nonagent_pod_spec.get('selector', {})
for k, v in non_agent_selector.items():
    nonagent.node_selector(key=k, value=v)
nonagent.add_toleration(key='surreal', operator='Exists', effect='NoExecute')
nonagent.image_pull_policy('Always')

for name, repo in images_to_build.items():
    builder = DockerBuilder.from_dict(self.docker_build_settings[name])
    builder.build()
    builder.tag(repo, exp.name)
    builder.push(repo, exp.name)

cluster.launch(exp, force=force, dry_run=dry_run)
```

