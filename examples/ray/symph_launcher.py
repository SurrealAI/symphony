from symphony.engine import Cluster

NAME = 'ray-test'

cpu_image = 'us.gcr.io/surreal-dev-188523/jimfan-cpu:latest'
gpu_image = 'us.gcr.io/surreal-dev-188523/jimfan-gpu:latest'

cluster = Cluster.new('kube') # cluster is a TmuxCluster
exp = cluster.new_experiment(NAME, port_range=[7070]) # exp is a TmuxExperimentSpec
master = exp.new_process(
    'master',
    args=['--py', 'ray/ray_master.py'],
    container_image=cpu_image
)
master.binds('redis-server')

for i in range(4):
    proc = exp.new_process(
        'worker{}'.format(i),
        container_image=cpu_image,
        # args=['--bash', 'ray/ray_worker.sh', i]
        args=['--py', 'ray/ray_worker.py', i]
    )
    proc.connects('redis-server')
    # proc.resource_request(cpu=1)

cluster.launch(exp)