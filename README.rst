Symphony: An orchestrating Library Supporting Multiple Backends
===============================================================

Symphony aims to ease the process of launching and monitoring
multi-process / multi-node computation tasks. It provides a simple
abstraction for launching multiple processes in a centralized place and
supports multiple backends (e.g. tmux and kubernetes). It also provides
a set of essential commandline interfaces to monitor the status of the
processes involved.

Index
=====

| `Motivation <#motivation>`__
| `Concepts <#processes-experiments-clusters>`__
| `Networking <#networking>`__
| `Monitoring <#monitoring-through-the-commandline>`__
| `Config <#config>`__
| `Using Symphony for your
  project <#using-symphony-as-part-of-your-project>`__

replay\_host = os.environ['SYMPH\_REPLAY\_SERVER\_HOST'] replay\_port =
os.environ['SYMPH\_REPLAY\_SERVER\_PORT'] server =
ReplayServer(host=replay\_host, port=replay\_port) ... \`\`\` And
similarly you can connect to this address in agent.

A process can declare networking in three ways: ``bind``, ``connect``,
``expose``. \* ``process.bind('service')`` tells symphony to assign a
port to ``service-1`` and expose both DNS address and port so that other
processes can connect to the binding process. All pocesses will have
access to environment variables ``SYMPH_SERVICE_1_HOST`` and
``SYMPH_SERVICE_1_PORT``. One can also do
``process.bind({'tensorboard': 6006})`` where a specific port is
assigned. \* ``connect`` to something (e.g. ``service-1``) declares that
the process expects some other process to ``bind`` to it. While the
envorinment variables for the host/port will still be provided at run
time (assuming that you did bind) even if you didn't call ``connect``,
it is recommended as connecting to some non-existent name will be caught
and cause the program to fail during declaration, before the experiment
even starts. \* ``expose`` is used when you are running experiments on a
cloud. It tells symphony to expose this port to a global ip. If you have
a process expose ``tensorboard`` you can later use
``symphony visit tensorboard`` to retrieve an ip and open a browser for
it. There will also be environment variables ``SYMPH_TENSORBOARD_HOST``
and ``SYMPH_TENSORBOARD_PORT``.

Monitoring Through the Commandline.
===================================

After you start running and experiment, symphony provides a convenient
commandline interface to know how each of the processes are running. The
script installed with symphony is mainly used for demonstration and
prototyping. For your own project, you can merge the interface with your
python script easily. See #\ `this
example <using-symphony-as-part-of-your-project>`__.

-  ``symphony process`` or ``symphony p`` lists the status of processes
   in an experiment.

   .. code:: bash

       $> symphony p
       Group     Name         Ready  Restarts  State           
             agent-0      1      0         running: 23.2h  
             eval-0       1      0         running: 23.2h   
       ...

-  ``symphony logs <process_name>`` retrieves logs from a given process.

   .. code:: bash

       $> symphony logs agent-0
       Agent starting ...

-  ``symphony list-experiments`` (``symphony ls``) lists all running
   experiments.

   .. code:: bash

       $> symphony ls
       experiment-0
       experiment-1
       ...

-  ``symphony delete`` (``symphony d``), ``symphony delete-batch``
   (``symphony db``) terminates experiments.
-  ``symphony visit [exposed_service]`` (``symphony vi``) opens a web
   browser to the exposed service (Use ``--url-only`` to only get the
   url).
-  Other convenient functionalities can be used for some clusters, (e.g.
   Kubernetes). ``exec, ssh, scp``.
-  If you are using a process group and that process names are not
   unique, use ``process_group/process`` in place of ``process``.

Config
======

Symphony provides several optional functionalities to help organize
experiments. They are controlled by ``SymphonyConfig`` singleton.

.. code:: python

    from symphony.engine import SymphonyConfig

-  ``set_username(name)`` makes all subsequently created experiments
   prepend username

   .. code:: python

       SymphonyConfig().set_username('sarah')
       cluster = Cluster.new('tmux') # cluster is a TmuxCluster
       exp1 = cluster.new_experiment('rl') # exp is a TmuxExperimentSpec
       print(exp1.name) # 'sarah-rl' 

-  ``set_experiment_folder(directory)`` saves all subsequently launched
   experiment specs to ``directory``. You can retrieve your declaration
   of experiments later. It also allows the cluster to complain to you
   if you are going to overwrite an existing experiment. (You can still
   pass 'force=True' to force overwrite)

   .. code:: python

       SymphonyConfig().set_experiment_folder('~/foo')
       cluster = Cluster.new('tmux') # cluster is a TmuxCluster
       exp1 = cluster.new_experiment('rl') # exp is a TmuxExperimentSpec
       cluster.launch(exp1) 
       # information about this experiment will be saved to ~/foo/rl

Using symphony as part of your project
======================================

To use symphony for your own project, the easiest way is to extend the
provided parser. You only need to do three things in a class that
extends ``SymphonyParser``: 1. Overwrite ``create_cluster(self)``,
define the backend that you want to use 2. Overwrite ``setup(self)``,
add a new subcommand for launch (so you can launch things) and
(optionally) set configs 3. Declare your experiment and launch it. (Here
we show how to add it as another subcommand of the script.)

.. code:: python

    # myproject.py
    from symphony.commandline import SymphonyParser
    from symphony.engine import Cluster
    from symphony.kube import KubeCluster
    import sys

    class MyProjectParser(SymphonyParser):
        def create_cluster(self): # step 1
            return Cluster.new('kube')

        def setup(self): # step 2
            super().setup()
            SymphonyConfig().set_username('sarah')
            parser = self.add_subparser('create') 
            # add subcommand: `python myproject.py create`
            # This subcommand is mapped to self.action_create(args)
            parser.add_argument(...)

        def action_create(self, args): # step 3
            exp = self.cluster.new_experiment('foo')
            p = exp.new_process(...)
            ...
            self.cluster.launch(exp)

    if __name__ == '__main__':
    MyProjectParser().main()

Now not only can you do ``python myproject.py create`` to launch an
experiment, but you can also use ``python myproject.py process`` to
monitor the processes of your experiment.
