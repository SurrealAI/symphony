# Docker builder
When building a Docker image, you are by default now allowed to reference different locations in a file system. This can be very problematic if you a re building an application with several custom dependencies in private repos. `symphony.DockerBuilder` provides a easy solution to this problem.

## Settings
Each docker build contains a setting. Here is an example in yaml format.
```yaml
temp_directory: ~/symph_temp/cpu
verbose: true # (prints docker cmdline output)
dockerfile: ~/surreal/Surreal/container/DockerfileCPU
context_directories: # These paths will be copied to temp_directory before build
  - name: surreal # Directory will be under folder @name in the build context
    path: ~/surreal/Surreal
    force_update: true # Copy a new version every time
  - name: mjkey.txt
    path: ~/.mujoco/mjkey.txt
    force_update: false
```
* `temp_directory` is the location where we construct the build context for docker. To ensure we don't accidentally include a lot of file, the docker builder will create a sub-folder where `docker build` is run in.
* `verbose` controls how much output is showed. It is `True` by default.
* `dockerfile` points to the dockerfile of the build
* `context_directories` is a list of dictionaries. Specifying what files or directories to fetch for the build process.
* Each dictionary in the `context_directories` list has three attributes:
    - `name`: What the name of the file or directories in the build context.
    - `path`: Where to copy from. If it is a file, it is moved to `name` in the build folder. If it is a directory, the entire tree is copied.
    - `force_update`: If the file or directory already exists in the build context (e.g. from the last build), `force_update=True` will remove the existing files and copy from the file system again. `force_update=False` will use the cached versions. This is used to help speed up the build process when there are several custom libraries but only one is being actively worked on.

## Using the docker builder
You can load the settings in a dictionary and use it to initialize the docker builder. This builder can then build, tag and push the image.
```python
from symphony import DockerBuilder

dockerfile = '~/surreal/symphony/test/test_docker_Dockerfile'
context_directories = [
    {
        'name': 'surreal',
        'path': '~/surreal/Surreal',
        'force_update': False,
    },
    {
        'name': 'tensorplex',
        'path': '~/surreal/Tensorplex',
        'force_update': True,
    }
]
temp_directory = '~/symph_tmp/'
repo = 'my_repo'
tag = 'latest'

builder = DockerBuilder(dockerfile, context_directories, temp_directory, verbose=True)

builder.build()

builder.tag(repo, tag)

builder.push(repo, tag)
```
