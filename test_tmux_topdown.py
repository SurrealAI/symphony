import unittest
import libtmux

from symphony.engine import *
from symphony import tmux


class TestTmuxCluster(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
      # TODO: Use mock.
      # Change the default Tmux server name, so it can be cleaned up.
      cls._server_name = tmux.cluster._SERVER_NAME
      tmux.cluster._SERVER_NAME = '__symphony_test__'
      cls.server = libtmux.Server(socket_name='__symphony_test__')

    @classmethod
    def tearDownClass(self):
        self.server.kill_server()
        tmux.cluster._SERVER_NAME = self._server_name
  
    def setUp(self):
        pass
  
    def tearDown(self):
        for sess in self.server.sessions:
            sess.kill_session()
  
    def test_launch_experiment(self):
        # Create specs.
        cluster = Cluster.new('tmux')
        exp = cluster.new_experiment('exp')
        group = exp.new_process_group('group')
        echo_proc = group.new_process('echo_proc', 'echo Hello World!')
        lone_proc = exp.new_process('lone_proc', 'echo I am alone')
    
        # Launch the experiment and verify it was successful.
        cluster.launch(exp)

        # TODO: finish the asserts
        self.assertEqual(len(self.server.sessions), 1)
        sess = self.server.sessions[0]
        self.assertEqual(sess.name, 'exp')


if __name__ == '__main__':
    unittest.main()


# learner.binds('myserver')
# replay.connects('myserver')
#
# agents = []
# for i in range(8):
#     agent = exp.new_process('agent' + str(i), '--cmd')
#     agent.connects('myserver')
#     agents.append(agent)
#
# tb = exp.new_process('tb', '--logdir')
# tb.exposes('tensorboard')

# cluster.launch(exp)
