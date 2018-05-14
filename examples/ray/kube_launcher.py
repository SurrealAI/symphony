import argparse
from symphony.engine import Cluster
from symphony.ray import *


USE_SURREAL = 1
MASTER_SCRIPT = 'ray_pong.py'
SATELLITE_SCRIPT = 'ray_satellite.py'
PORTS = list(range(9000, 9500))


parser = argparse.ArgumentParser()
parser.add_argument('name', type=str, nargs='?', default='ray')
parser.add_argument('-s', '--satellites', default=4, type=int)
args = parser.parse_args()


cpu_image = 'us.gcr.io/surreal-dev-188523/jimfan-cpu:latest'
gpu_image = 'us.gcr.io/surreal-dev-188523/jimfan-gpu:latest'

cluster = Cluster.new('raykube')
exp = cluster.new_experiment(args.name, port_range=PORTS)
master = exp.new_master_process(
    num_satellites=args.satellites,
    args=['python', '-u', MASTER_SCRIPT],
    container_image=cpu_image,
)

if USE_SURREAL:
    # master is just a driver that doesn't run code
    master.node_selector(key='surreal-node', value='agent')
    master.resource_request(cpu=1.5)


# DEMO ONLY otherwise won't be much faster than serial version
limit_numpy_env = {
    "MKL_NUM_THREADS": 1,
    "OPENBLAS_NUM_THREADS": 1
}

for i in range(args.satellites):
    satellite = exp.new_satellite_process(
        id=i,
        container_image=cpu_image,
        # args=['--bash', 'ray/ray_worker.sh', i]
        args=['python', '-u', SATELLITE_SCRIPT],
        resources={'mujoco': 15},
        env=limit_numpy_env,
    )

    if USE_SURREAL:
        satellite.node_selector(key='surreal-node', value='nonagent-cpu')
        satellite.resource_request(cpu=7.5)


for proc in exp.list_processes():
    proc.add_toleration(key='surreal', operator='Exists', effect='NoExecute')


cluster.launch(exp)