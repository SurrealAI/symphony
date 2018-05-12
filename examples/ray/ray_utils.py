import os
import ray
import time
import shlex
import json


def init_master_node(resources=None, **ray_kwargs):
    """
    http://ray.readthedocs.io/en/latest/api.html#ray.init

    Args:
        resources: dict of resources for master node. You can include "gpu"
        **ray_kwargs: other kwargs passed to ray.init()
    """
    port = os.environ['SYMPH_MASTER_REDIS_PORT']
    if resources is None:
        resources = {}
    assert isinstance(resources, dict)
    resources = resources.copy()
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

    ray.init(redis_address='localhost:'+port, **ray_kwargs)


def flush_redis_unsafe():
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