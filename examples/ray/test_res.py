"""
Test resources
"""

import ray
import time


ray.init(redis_address='localhost:8060')


@ray.remote(resources={'mujoco': 3})
def f1(arg):
    print('ARG', arg, 'IP', ray.services.get_node_ip_address())
    for i in range(5):
        print('alive', i)
        time.sleep(0.5)
    return 'done'


for b in range(100):
    print('batch', b)
    ray.get([f1.remote(i) for i in range(8)])

print('ALL DONE')