# Example: ZMQ + NFS

This folder contains example for you to run a simple client-server pair on both tmux and kubernetes with NFS.

Configure NFS on GCE Kubernetes with [single node FS deployment](https://console.cloud.google.com/launcher/details/click-to-deploy-images/singlefs).

The Dockerfile and `build_docker_image.py` are very similar to `examples/zmq`, please refer to that directory's README. You need to rebuild and push the docker image whenever you update the code.

Please configure the NFS settings in `nfs_settings.py`.

- `run_simple_client.py` will write messages to `<DEMO_FOLDER>/client.txt` defined in the settings.
- `run_simple_server.py` will both print to stdout and write messages to `<DEMO_FOLDER>/server.txt`.


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
