"""
This driver should be run as a standalone executable on a worker node.
Worker nodes are only responsible for starting satellite ray servers that talk
to the master server. They do not run any algorithm code directly.

Assumes the following environment variables:
- SYMPH_MASTER_REDIS_ADDR: master ray address, set up by symphony AddressBook
- SYMPH_RAY_RESOURCE: resource dict as a JSON string
- SYMPH_RAY_ID: ID of this satellite script
"""
import os
import sys
import shlex
import time
import subprocess
import json


def print_err(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)


for env_name in ['SYMPH_RAY_ID', 'SYMPH_RAY_RESOURCE', 'SYMPH_MASTER_REDIS_ADDR']:
    if env_name not in os.environ:
        print_err('missing critical env variable:', env_name)
        sys.exit(1)


satellite_id = os.environ['SYMPH_RAY_ID']
print('Symphony-Ray satellite ID:', satellite_id)

resource_str = os.environ['SYMPH_RAY_RESOURCE']

# must be a valid JSON string
resources = json.loads(resource_str)
print('tagged resources:', resources)

# try starting ray connection and loop until success
success = False
MAX_TRIALS = 30
trials = 0
MAX_SLEEP = 60
current_sleep = 2.

while not success and trials < MAX_TRIALS:
    proc = subprocess.run(
        'ray start --redis-address=$SYMPH_MASTER_REDIS_ADDR --resources={} --plasma-directory /dev/shm'
        .format(shlex.quote(resource_str)),
        shell=True
    )
    exitcode = proc.returncode
    success = exitcode == 0
    if not success:
        print_err(
            '\n', '=' * 10,
            'Trial #{}: ray init failure exit code {}'.format(trials, exitcode),
            '='*10
        )
        print_err('retry ...\n\n')
        time.sleep(min(MAX_SLEEP, current_sleep))
        current_sleep *= 1.5
    trials += 1

if success:
    while True:  # process waits indefinitely to keep pod alive
        print(time.strftime('Satellite {} alive: %D %H:%M:%S'.format(satellite_id)))
        time.sleep(3600)
else:
    print_err('Reached max number of unsuccessful trials. '
              'Connection to Ray master server cannot be established.')
    sys.exit(1)
