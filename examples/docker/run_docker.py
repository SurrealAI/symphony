from pprint import PrettyPrinter
pprint = PrettyPrinter(indent=2).pprint
from symphony.docker import *
from symphony.engine import *


cluster = Cluster.new('docker')
#
# exp = cluster.new_experiment('exp1')
#
# servers = exp.new_process_group('server-group')
# clients = exp.new_process_group('client-group')
#
# server1 = servers.new_process('server-1', 'docker_server')
# client1 = clients.new_process('client-1', 'docker_client')
# client2 = exp.new_process('client-2', 'docker_client')
#
# client1.set_hostname('client-1')
# client1.set_env('TEST_PORT', 1234)
# client1.set_env('TEST_HOST', 'server-group--server-1')
# client2.set_hostname('client-2')
# client2.set_env('TEST_PORT', 1234)
# client2.set_env('TEST_HOST', 'server-group--server-1')
#
# server1.set_hostname('server-1')
# server1.set_env('TEST_PORT', 1234)
# server1.set_ports(['1234:4321', 10, 55555])
#
# cluster.launch(exp)
# cluster.delete(exp.name)
# print(cluster.list_experiments())
# pprint(cluster.describe_experiment(exp.name))
# pprint(cluster.describe_experiment('wtf'))
# pprint(cluster.describe_experiment('empty'))
# pprint(cluster.describe_process_group('exp1', 'server-group'))
# pprint(cluster.describe_process_group('empty', 'server-group'))
# pprint(cluster.describe_process('exp1', 'client-2'))
# cluster.get_log('exp1', 'server-1', follow=True, tail=10)
# print(cluster.exec_command('exp1', 'server-1', 'hostname'))

from symphony.commandline import SymphonyParser
from symphony.docker import DockerCluster
from symphony.engine import Cluster

class DockerParser(SymphonyParser):
    def create_cluster(self): # step 1
        # Create a Cluster with Docker Compose backend.
        return Cluster.new('docker')

    def setup(self): # step 2
        super().setup()

        # Subcommand create: `python run_docker.py create`
        # This subcommand is mapped to self.action_create
        parser = self.add_subparser('create')
        parser.add_argument('experiment_name', type=str)

        # Subcommand delete: `python run_docker.py delete`
        # This subcommand is mapped to self.action_delete

    def action_create(self, args):
        cluster = self.cluster

        # Create an Experiment.
        exp = cluster.new_experiment(args.experiment_name)

        # Create server and client processes.
        servers = exp.new_process_group('server-group')
        server1 = servers.new_process('server-1', 'docker_server')

        clients = exp.new_process_group('client-group')

        client1 = clients.new_process('client-1', 'docker_client')
        client1.set_hostname('client-1')
        client1.set_env('TEST_PORT', 1234)
        client1.set_env('TEST_HOST', 'server-group--server-1')

        client2 = exp.new_process('client-2', 'docker_client')
        client2.set_hostname('client-2')
        client2.set_env('TEST_PORT', 1234)
        client2.set_env('TEST_HOST', 'server-group--server-1')

        # Configure ports.
        server1.set_hostname('server-1')
        server1.set_env('TEST_PORT', 1234)
        server1.set_ports(['1234:4321', 10, 55555])

        # Launch.
        cluster.launch(exp)

    def action_delete(self, args):
        cluster = self.cluster
        cluster.delete(args.experiment_name)


if __name__ == '__main__':
    DockerParser().main()
