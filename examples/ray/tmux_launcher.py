import argparse
from symphony.engine import Cluster
from pprint import pprint


parser = argparse.ArgumentParser()
parser.add_argument('name', type=str, nargs='?', default='raylocal')
parser.add_argument('-w', '--workers', default=4, type=int)
args = parser.parse_args()


cluster = Cluster.new('tmux') # cluster is a TmuxCluster
exp = cluster.new_experiment(args.name, port_range=[7070]) # exp is a TmuxExperimentSpec
master = exp.new_process(
    'master',
    cmds=['python ray_master.py'],
)
master.binds('redis-server')


for i in range(args.workers):
    worker = exp.new_process(
        'worker{}'.format(i),
        cmds='python ray_worker.py {}'.format(i)
    )
    worker.connects('redis-server')


cluster.launch(exp)