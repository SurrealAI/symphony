"""
Helper functions that can be used in the driver script
"""
import os
import ray
import time
import shlex
import json
from .symph_envs import *


def ray_init_master_node(**ray_kwargs):
    """
    http://ray.readthedocs.io/en/latest/api.html#ray.init

    Args:
        resources: dict of resources for master node. You can include "gpu"
        **ray_kwargs: other kwargs passed to ray.init()
    """
    port = ray_master_redis_port()
    resources = ray_resources()
    if 'gpu' in resources:
        num_gpus = int(resources.pop('gpu'))
        gpu_option = '--num-gpus={}'.format(num_gpus)
    else:
        gpu_option = ''
    resources = shlex.quote(json.dumps(resources))
    # os.system('ray start --head {} --redis-port={} --resources={} --plasma-directory /mnt/hugepages --huge-pages'
    #           .format(gpu_option, port, resources))
    os.system('ray start --head {} --redis-port={} --resources={}'
              .format(gpu_option, port, resources))

    time.sleep(50)

    ray.init(redis_address='localhost:{}'.format(port), **ray_kwargs)


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
