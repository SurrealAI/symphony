import symphony
from symphony.engine import Cluster


cluster = Cluster.new('subproc',
                      stdout_mode='print', stderr_mode='print', log_dir=None)
exp = cluster.new_experiment('hello-world')
server = exp.new_process('server', cmd='python simple_server.py')
client = exp.new_process('client', cmd='python simple_client.py')
server.binds('example')
client.connects('example')

print('Server and client are running in subprocess mode')
cluster.launch(exp, dry_run=False)
