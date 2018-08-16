# Example usage of Symphony with Docker Compose backend
This folder contains an example usage of Docker Compose backend for locally running a simple client-server pair.

## Step 1: Install dependencies.

Make sure you have symphony installed in your python environment
and that the Docker daemon is running.
Docker Compose backend also depends on the `docker` package:
```bash
pip install docker
```

## Step 2: Build Docker images to run.

The two folders `client` and `server` contain `Dockerfile`s that are ready
to be used to Docker images:
```bash
docker build -t docker_client -f client/Dockerfile
docker build -t docker_server -f server/Dockerfile
```

## Step 3: Launch the experiment.

Now we are ready to launch the experiment!
```bash
python run_docker.py create test_exp
python run_docker.py list-experiments
```

You should see the output `test_exp`, verifying that the experiment is running.

## Step 4: Interact with processes.

You can check the output from the server and client processes:

### Server
```bash
python run_docker.py logs server-1 test_exp
```

### Clients
```bash
python run_docker.py logs client-1 test_exp
python run_docker.py logs client-2 test_exp
```

## Step 5: Clean up.

After we are done, we can delete the experiment.
```bash
python run_docker.py delete test_exp
python run_docker.py list-experiments
```

This will print out nothing, verifying that the experiment has been deleted.
