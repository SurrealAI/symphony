import argparse
from symphony.engine import Cluster
from pprint import pprint


USE_SURREAL = 0


parser = argparse.ArgumentParser()
parser.add_argument('name', type=str, nargs='?', default='ray')
parser.add_argument('-w', '--workers', default=4, type=int)
args = parser.parse_args()


cpu_image = 'us.gcr.io/surreal-dev-188523/jimfan-cpu:latest'
gpu_image = 'us.gcr.io/surreal-dev-188523/jimfan-gpu:latest'

cluster = Cluster.new('kube') # cluster is a TmuxCluster
exp = cluster.new_experiment(args.name, port_range=[7070]) # exp is a TmuxExperimentSpec
master = exp.new_process(
    'master',
    args=['--py', 'ray_master.py'],
    container_image=cpu_image
)
master.binds('redis-server')
if USE_SURREAL:
    master.node_selector(key='surreal-node', value='nonagent-cpu')
    master.resource_request(cpu=7)


for i in range(args.workers):
    worker = exp.new_process(
        'worker{}'.format(i),
        container_image=cpu_image,
        # args=['--bash', 'ray/ray_worker.sh', i]
        args=['--py', 'ray_worker.py', i]
    )
    worker.connects('redis-server')
    if USE_SURREAL:
        worker.node_selector(key='surreal-node', value='agent')
        worker.resource_request(cpu=1.5)


for proc in exp.list_processes():
    proc.add_toleration(key='surreal', operator='Exists', effect='NoExecute')


# pprint(exp.dump_dict())

cluster.launch(exp)