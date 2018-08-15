from symphony.engine import Cluster
from symphony.kube import KubeCluster
from symphony.commandline import SymphonyParser

UPSTREAM_URL_ROOT = 'us.gcr.io/jimfan2018-208323/symphony-demo'


class KubeParser(SymphonyParser):
    def create_cluster(self): # step 1
        return Cluster.new('kube')

    def setup(self): # step 2
        super().setup()
        parser = self.add_subparser('create')
        parser.add_argument('experiment_name', type=str)
        # add subcommand: `python run_kube.py create`
        # This subcommand is mapped to self.action_create(args)

    def action_create(self, args):
        cluster = self.cluster
        exp = cluster.new_experiment(args.experiment_name)
        client = exp.new_process(
            'client',
            container_image=UPSTREAM_URL_ROOT+':latest',
            command=['python'],
            args=['-u', '/run_simple_client.py']
        )
        server = exp.new_process(
            'server',
            container_image=UPSTREAM_URL_ROOT+':latest',
            command=['python'],
            args=['-u', '/run_simple_server.py']
        )
        # Good to have when you are doing development
        client.image_pull_policy('Always')
        server.image_pull_policy('Always')
        
        server.binds('example')
        client.connects('example')
        cluster.launch(exp)

if __name__ == '__main__':
    print("---")
    print("Use command `python run_kube.py create` to create an experiment")
    print("---")
    print("Use command `python run_kube.py lsp` to see the status of pods")
    print("---")
    print("Use command `python run_kube.py logs server` (or client) to see logs")
    print("---")
    print("Use command `python run_kube.py delete` to delete your experiment")
    print("---")
    KubeParser().main()