"""
Helper functions that can be used in the driver script
"""
import os
import ray
import time
import shlex
import json
import nanolog as nl
from .symph_envs import *
from symphony.zmq import ZmqServer


def ray_init_master_node(**ray_kwargs):
    """
    Should be called _before_ any training code.
    Custom resources and Redis address will be passed as env vars by symphony's
    RayKubeCluster.

    1. Ray master starts, but don't execute any training code.
    2. All ray workers need to start, and tell master they are up.
        No worker can start _before_ master starts.
    3. After Ray master hears back from all worker nodes, it will unblock and
        continue to execute training code
    http://ray.readthedocs.io/en/latest/api.html#ray.init

    Args:
        **ray_kwargs: other kwargs passed to ray.init()
    """
    port = ray_master_redis_port()
    resources = ray_resources()
    num_satellites = ray_num_satellites()
    if 'gpu' in resources:
        num_gpus = int(resources.pop('gpu'))
        gpu_option = '--num-gpus={}'.format(num_gpus)
    else:
        gpu_option = ''
    resources = shlex.quote(json.dumps(resources))
    os.system('ray start --head {} '
              '--redis-port={} '
              '--resources={} '
              # '--plasma-directory /mnt/hugepages --huge-pages'
              .format(gpu_option, port, resources))

    log = nl.Logger('zmq')  # existing log from zmq.structs
    # sync master and satellite nodes
    sync_server = ZmqServer(
        host='*', port=ray_zmq_port(), deserializer='json'
    )
    log.info('Expecting', num_satellites, 'satellites.')
    # will not proceed until all satellites have connected
    for i in range(num_satellites):
        log.info(sync_server.recv())  # blocking
        log.infofmt('Heard back from {} satellite{} so far',
                    i+1, 's' if i > 0 else '')
        sync_server.send('master alive: ' + ray_ip_address())

    ray.init(redis_address='localhost:{}'.format(port), **ray_kwargs)
    log.infobanner('Driver initialized', banner_lines=3)
    log.infopp(ray_client_table(), width=400, compact=True)


def ray_client_table():
    """
    Useful for checking satellite node connection status
    """
    return ray.global_state.client_table()


def ray_ip_address():
    """
    Get current code IP address
    """
    return ray.services.get_node_ip_address()


def ray_flush_redis_unsafe():
    """
    EXPERIMENTAL ONLY!
    From Ray googlegroup
    """
    if not hasattr(ray.worker.global_worker, "redis_client"):
        raise Exception("ray.experimental.flush_redis_unsafe cannot be called "
                        "before ray.init() has been called.")

    redis_client = ray.worker.global_worker.redis_client

    # Delete the log files from the primary Redis shard.
    keys = redis_client.keys("LOGFILE:*")
    if len(keys) > 0:
        num_deleted = redis_client.delete(*keys)
    else:
        num_deleted = 0
    print("Deleted {} log files from Redis.".format(num_deleted))

    # Delete the event log from the primary Redis shard.
    keys = redis_client.keys("event_log:*")
    if len(keys) > 0:
        num_deleted = redis_client.delete(*keys)
    else:
        num_deleted = 0
    print("Deleted {} event logs from Redis.".format(num_deleted))
