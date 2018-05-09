from symphony.engine import Cluster

cpu_image = 'us.gcr.io/surreal-dev-188523/jimfan-cpu:latest'
gpu_image = 'us.gcr.io/surreal-dev-188523/jimfan-gpu:latest'

cluster = Cluster.new('kube') # cluster is a TmuxCluster
exp = cluster.new_experiment('testray', port_range=[7070]) # exp is a TmuxExperimentSpec
master = exp.new_process(
    'master', command='python',
    args=['--py', 'ray_master.py'],
    container_image=cpu_image
)
master.binds('redis')

for i in range(4):
    proc = exp.new_process(
        'worker{}'.format(i),
        container_image=cpu_image,
        args=['--bash', 'ray_worker.sh']
    )
    proc.connects('redis')

cluster.launch(exp)