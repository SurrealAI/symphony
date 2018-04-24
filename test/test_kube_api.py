from symphony.kube import *

cluster = Cluster.new('kube', dry_run=False)
print('experiments')
exps = cluster.list_experiments()
print(exps)
exp = exps[-1]
# cluster.list_processes(exp)
print('process_groups')
pgs = cluster.list_process_groups(exp)
print(pgs)
print('processes')
pcs = cluster.list_processes(exp, 'nonagent')
print(pcs)
print('topology')
t = cluster.list_topology(exp)
print(t)
