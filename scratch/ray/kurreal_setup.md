
```python
assert agent_pod_type in C.pod_types, \
    'agent pod type not found in `pod_types` section in ~/.surreal.yml'
assert nonagent_pod_type in C.pod_types, \
    'nonagent pod type not found in `pod_types` section in ~/.surreal.yml'
agent_pod_spec = C.pod_types[agent_pod_type]
nonagent_pod_spec = C.pod_types[nonagent_pod_type]
agent_resource_request = agent_pod_spec.get('resource_request', {})
nonagent_resource_request = nonagent_pod_spec.get('resource_request', {})
agent_resource_limit = agent_pod_spec.get('resource_limit', {})
nonagent_resource_limit = nonagent_pod_spec.get('resource_limit', {})

cluster = Cluster.new('kube')

exp = cluster.new_experiment(experiment_name)

nonagent = exp.new_process_group('nonagent')
learner = nonagent.new_process('learner',
                               container_image=nonagent_pod_spec.image,
                               args=['--cmd', cmd_dict['learner']])
replay = nonagent.new_process('replay', container_image=nonagent_pod_spec.image,
                              args=['--cmd', cmd_dict['replay']])
ps = nonagent.new_process('ps', container_image=nonagent_pod_spec.image,
                          args=['--cmd', cmd_dict['ps']])
tensorboard = nonagent.new_process('tensorboard',
                                   container_image=nonagent_pod_spec.image,
                                   args=['--cmd', cmd_dict['tensorboard']])
tensorplex = nonagent.new_process('tensorplex',
                                  container_image=nonagent_pod_spec.image,
                                  args=['--cmd', cmd_dict['tensorplex']])
loggerplex = nonagent.new_process('loggerplex',
                                  container_image=nonagent_pod_spec.image,
                                  args=['--cmd', cmd_dict['loggerplex']])

agents = []
for i, arg in enumerate(cmd_dict['agent']):
    agent_p = exp.new_process('agent-{}'.format(i),
                              container_image=agent_pod_spec.image,
                              args=['--cmd', arg])
    agents.append(agent_p)

evals = []
for i, arg in enumerate(cmd_dict['eval']):
    eval_p = exp.new_process('eval-{}'.format(i),
                             container_image=agent_pod_spec.image,
                             args=['--cmd', arg])
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

if mujoco:
    mjkey = file_content(C.mujoco_key_path)

for proc in exp.list_all_processes():
    # Mount nfs
    proc.mount_nfs(server=nfs_server, path=nfs_server_path,
                   mount_path=nfs_mount_path)

    # mount git
    # This needs fixing, currently it has a lot of assumptions,
    # including that direcotry name of the repo locally should equal to cloud
    # which can be false
    for git_repo in repo_names:
        # if git_repo == 'surreal':
        #     git_repo_name_github='Surreal'
        # elif git_repo == 'tensorplex':
        #     git_repo_name_github='Tensorplex'
        # else:
        #     git_repo_name_github=git_repo
        repository = 'https://{}:{}@github.com/SurrealAI/{}'.format(
            C.git.user, C.git.token, git_repo)
        revision = C.git.snapshot_branch
        mount_path = '/mylibs/{}'.format(git_repo)
        proc.mount_git_repo(repository=repository, revision=revision,
                            mount_path=mount_path)
        env_key = 'repo_{}'.format(git_repo.replace('-', '_'))
        env_val = '/mylibs/{0}/{0}'.format(git_repo)
        proc.set_env(env_key, env_val)

    # Add mujoco key: TODO: handle secret properly
    proc.set_env('mujoco_key_text', mjkey)
    proc.image_pull_policy('Always')

agent_selector = agent_pod_spec.get('selector', {})
for proc in itertools.chain(agents, evals):
    proc.resource_request(cpu=1.5)
    proc.add_toleration(key='surreal', operator='Exists', effect='NoExecute')
    proc.restart_policy('Never')
    # required services
    for k, v in agent_selector.items():
        proc.node_selector(key=k, value=v)
    proc.resource_request(**agent_resource_request)
    proc.resource_limit(**agent_resource_limit)

learner.set_env('DISABLE_MUJOCO_RENDERING', "1")
learner.resource_request(**nonagent_resource_request)
if 'nvidia.com/gpu' in nonagent_resource_limit:
    # Note/TODO: We are passing resource limits as kwargs, so '/' cannot happen here
    # Should we change this?
    nonagent_resource_limit['gpu'] = nonagent_resource_limit['nvidia.com/gpu']
    del nonagent_resource_limit['nvidia.com/gpu']
learner.resource_limit(**nonagent_resource_limit)

non_agent_selector = nonagent_pod_spec.get('selector', {})
for k, v in non_agent_selector.items():
    nonagent.node_selector(key=k, value=v)
nonagent.add_toleration(key='surreal', operator='Exists', effect='NoExecute')
nonagent.image_pull_policy('Always')

cluster.launch(exp, force=force, dry_run=dry_run)
```

