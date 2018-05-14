import os
import ray
import time
import shlex
import json

from symphony.ray import *


ray_init_master_node()


def get_ip():
    time.sleep(0.02)
    return ray.services.get_node_ip_address()


def schedule_to_node(func, i):
    """
    Wrapper
    Schedules a function to a specific node by hacking "resources"

    Args:
        i: int, if None then schedule to any node is possible
    """
    # func = deepcopy_func(func)
    if i is None:
        return ray.remote(func)
    return ray.remote(resources={'tag{}'.format(i): 1})(func)


print('SUCCESSFULLY STARTED', '='*50)


def run_get_ips():
    # Get a list of the IP addresses of the nodes that have joined the cluster.
    f_anywhere = schedule_to_node(get_ip, None)
    return list(set(ray.get([f_anywhere.remote() for _ in range(1000)])))


def f0(): return get_ip()
def f1(): return get_ip()
def f2(): return get_ip()
def f3(): return get_ip()


def run_resource_alloc():
    # force schedule to each of 4 workers
    # funcs = [schedule_to_node(get_ip, i) for i in range(4)]
    funcs = [schedule_to_node(ff, i) for i, ff in enumerate([f0,f1,f2,f3])]
    return ray.get([func.remote() for func in funcs])


while True:
    time.sleep(10)
    print('QUERY WORKERS')
    # print(run_resource_alloc())
    print(run_get_ips())
