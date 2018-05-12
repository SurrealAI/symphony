import argparse
from symphony.engine import Cluster
from pprint import pprint
import json


USE_SURREAL = 1
MASTER_SCRIPT = 'ray_pong.py'
MASTER_ADDR = 'master-redis'
LIMIT_NUMPY = True


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
    args=['--py', MASTER_SCRIPT],
    container_image=cpu_image,
    env={'SYMPH_RAY_ID': 'master'}
)
master.binds(MASTER_ADDR)
master.mount_shared_memory()

if USE_SURREAL:
    # master is just a driver that doesn't run code
    master.node_selector(key='surreal-node', value='agent')
    master.resource_request(cpu=1.5)


# DEMO ONLY otherwise won't be much faster than serial version
limit_numpy_env = {
    "MKL_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1"
}

for i in range(args.workers):
    env = {'SYMPH_RAY_ID': str(i),
           'SYMPH_RAY_RESOURCE': json.dumps({'mujoco': 15})}
    env.update(limit_numpy_env)

    worker = exp.new_process(
        'worker{}'.format(i),
        container_image=cpu_image,
        # args=['--bash', 'ray/ray_worker.sh', i]
        args=['--py', 'ray_satellite.py'],
        env=env
    )
    worker.connects(MASTER_ADDR)
    worker.mount_shared_memory()

    if USE_SURREAL:
        worker.node_selector(key='surreal-node', value='nonagent-cpu')
        worker.resource_request(cpu=7.5)


for proc in exp.list_processes():
    proc.add_toleration(key='surreal', operator='Exists', effect='NoExecute')


# pprint(exp.dump_dict())

cluster.launch(exp)