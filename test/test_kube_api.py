# from symphony.kube import *
# import json
# from benedict import BeneDict
# import pprint

# pp = pprint.PrettyPrinter(indent=4)

# cluster = Cluster.new('kube', dry_run=False)
# print('experiments')
# exps = cluster.list_experiments()
# print(exps)
# exp = exps[-1]
# # cluster.list_processes(exp)
# print('')
# print('describe_experiment')
# exp_res = BeneDict(cluster.describe_experiment(exp))
# pp.pprint(exp_res)

# print('')
# print('describe_process_group')
# pg = BeneDict(cluster.describe_process_group(exp, 'nonagent'))
# pp.pprint(pg)

# print('')
# print('describe_process')
# p = BeneDict(cluster.describe_process(exp, 'learner', 'nonagent'))
# p = BeneDict(cluster.describe_process(exp, 'agent-0'))
# pp.pprint(p)

# print('')
# print('external_service')
# ip = cluster.external_service(exp, 'tensorboard')
# print(ip)

# # print(json.loads(pgs[0]))
# # print('processes')
# # pcs = cluster.list_processes(exp, 'nonagent')
# # print(pcs)
# # print('topology')
# # t = cluster.list_topology(exp)
# # print(t)

