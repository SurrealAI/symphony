"""
This driver should be run as a standalone executable on a worker node.
Worker nodes are only responsible for starting satellite ray servers that talk
to the master server. They do not run any algorithm code directly.

Ray cluster must follow the starting order:

1. Ray master starts, but don't execute any training code.
2. All ray workers need to start, and tell master they are up.
    No worker can start _before_ master starts.
3. After Ray master hears back from all worker nodes, it will unblock and
    continue to execute training code

Assumes the following environment variables:
- SYMPH_RAY_MASTER_REDIS_ADDR: master ray address, set up by symphony AddressBook
- SYMPH_RAY_RESOURCE: resource dict as a JSON string
- SYMPH_RAY_ID: ID (rank) of this satellite script
"""
import os
import sys
import shlex
import time
import subprocess
import json
import nanolog as nl
from .driver import ray_ip_address
from .symph_envs import *
from symphony.zmq.communicator import ZmqClient


# TODO disable Transparent Huge Page (THP) in docker
# TODO --huge-pages option will cause plasma crash, not sure how to fix yet

def launch_satellite(log_file='satellite.out'):
    RAY_DIR = '/tmp/raylogs'
    os.makedirs(RAY_DIR, exist_ok=True)

    log = nl.Logger('zmq')  # existing log from zmq.structs
    log.info('Symphony-Ray satellite ID:', ray_id())

    resources = ray_resources()
    log.info('tagged resources:', resources)

    sync_client = ZmqClient(
        address=ray_zmq_addr(), serializer='json', deserializer='str'
    )

    # block until master is alive
    reply = sync_client.request({
        'status': 'alive', 'id': ray_id(),
        'ip': ray_ip_address(), 'resources': resources
    })
    log.info(reply, '... proceed to initialize Ray clients')

    if 'gpu' in resources:
        num_gpus = int(resources.pop('gpu'))
        gpu_option = '--num-gpus={}'.format(num_gpus)
    else:
        gpu_option = ''
    resource_str = shlex.quote(json.dumps(resources))

    # try starting ray connection and loop until success
    success = False
    MAX_TRIALS = 30
    trials = 0
    MAX_SLEEP = 60
    current_sleep = 2.

    while not success and trials < MAX_TRIALS:
        proc = subprocess.run(
            'ray start '
            '--redis-address="{}" '
            '{} '
            '--resources={} '
            '--plasma-directory /dev/shm'
            .format(ray_master_redis_addr(), gpu_option, resource_str),
            shell=True
        )
        exitcode = proc.returncode
        success = exitcode == 0
        if not success:
            log.warningbannerfmt(
                'Trial #{}: ray init failure exit code {}',
                trials, exitcode,
                banner_lines=3
            )
            time.sleep(min(MAX_SLEEP, current_sleep))
            current_sleep *= 1.5
        trials += 1

    if success:
        _ = sync_client.request({
            'status': 'connected', 'id': ray_id(),
            'ip': ray_ip_address(), 'resources': resources
        })
        log.info('Ray client initialized and connected, ready to roll')
        while True:  # process waits indefinitely to keep pod alive
            log.infofmt('Satellite {} alive', ray_id())
            time.sleep(3600)
    else:
        log.critical('Reached max number of unsuccessful trials. '
                     'Connection to Ray master server cannot be established.')
        sys.exit(1)


if __name__ == '__main__':
    launch_satellite()
