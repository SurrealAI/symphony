from pprint import PrettyPrinter
pprint = PrettyPrinter(indent=2).pprint

from symphony.docker import *
from symphony.engine import *


cluster = Cluster.new('docker')

exp = cluster.new_experiment('exp1')

servers = exp.new_process_group('server-group')
clients = exp.new_process_group('client-group')

server1 = servers.new_process('server-1', 'docker_server')
client1 = clients.new_process('client-1', 'docker_client')
client2 = exp.new_process('client-2', 'docker_client')

client1.set_hostname('client-1')
client1.set_env('TEST_PORT', 1234)
client1.set_env('TEST_HOST', 'server-group--server-1')
client2.set_hostname('client-2')
client2.set_env('TEST_PORT', 1234)
client2.set_env('TEST_HOST', 'server-group--server-1')

server1.set_hostname('server-1')
server1.set_env('TEST_PORT', 1234)
server1.set_ports(['1234:4321', 10, 55555])

cluster.launch(exp)
# cluster.delete(exp.name)
# print(cluster.list_experiments())
# pprint(cluster.describe_experiment(exp.name))
# pprint(cluster.describe_experiment('empty'))
# pprint(cluster.describe_process_group('exp1', 'server-group'))
# pprint(cluster.describe_process_group('empty', 'server-group'))
# pprint(cluster.describe_process('exp1', 'client-2'))
# cluster.get_log('exp1', 'server-1', follow=True, tail=10)
# print(cluster.exec_command('exp1', 'server-1', 'hostname'))
