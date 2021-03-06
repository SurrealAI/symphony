import symphony
from symphony.engine import Cluster
from symphony.tmux import TmuxCluster

cluster = Cluster.new('tmux', server_name='default')
exp = cluster.new_experiment('hello-world')
server = exp.new_process('server', cmds=['source activate symphony', 'python simple_server.py'])
client = exp.new_process('client', cmds=['source activate symphony', 'python simple_client.py'])
server.binds('example')
client.connects('example')
cluster.launch(exp)

print('Server and client are running in a tmux session')
print('Run `tmux a` to see your processes')
# Do tmux ls to see how things are going