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
    os.system('ray start --head {} --redis-port={} --resources={}'
              .format(gpu_option, port, resources))
    time.sleep(2)

    ray.init(redis_address='localhost:'+port)
