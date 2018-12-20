# Example usage of symphony
This folder contains example for you to run a simple client-server pair on both tmux and kubernetes

* First, please make sure you have symphony installed in your python environment. Also do 
```bash
pip install pyarrow
```

* Take a look at `simple_client.py`, `simple_server.py`, these are the files that we plan to run

* Next, go to `run_tmux.py`. This file runs the server and client on tmux. In line 6 and 7, change the `source activate ...` command to the corresponding ones that activates the correct python environment on your machine (or delete that command if it does not apply). After that, do
```bash
python run_tmux.py
tmux a
```
You should be able to see the client and server talking to each other.

Note that if you want to use a server name that isn't `"default"`, you will have to add `-L <your_server_name>` to all tmux commands. For example, `tmux ls` becomes `tmux -L my_awesome_server ls`

* We can also run the client-server pair using kubernetes. For surreal team members the shared cloud has an example built in (you can optionally look at `Dockerfile` and `build_docker_image.py` to see how it is done). The `run_kube.py` file contains a minimal example of what the main script of a project powered by symphony would look like. Use the following command to create an experiment
```bash
python run_kube.py create <experiment-name>
```
and explore the following commands
```bash
python run_kube.py lsp
python run_kube.py logs client
python run_kube.py logs server
```
To clean up, do
```bash
python run_kube.py delete
```
