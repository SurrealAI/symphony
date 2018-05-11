import os
import ray
import time
import shlex
import types
from benedict import dump_json_str

port = os.environ['SYMPH_REDIS_SERVER_PORT']
resources = shlex.quote(dump_json_str({'tag0': 0, 'tag1': 0}))
os.system('ray start --head --redis-port={} --resources={}'.format(port, resources))
time.sleep(2)

ray.init(redis_address='localhost:'+port)


def get_ip():
    time.sleep(0.02)
    return ray.services.get_node_ip_address()


def deepcopy_func(f, name=None):
    '''
    return a function with same code, globals, defaults, closure, and
    name (or provide a new name)
    '''
    fn = types.FunctionType(f.__code__, f.__globals__, name or f.__name__,
        f.__defaults__, f.__closure__)
    # in case f was given attrs (note this dict is a shallow copy):
    fn.__dict__.update(f.__dict__)
    return fn


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


def f0():
    time.sleep(0.02)
    return ray.services.get_node_ip_address()
def f1():
    time.sleep(0.02)
    return ray.services.get_node_ip_address()
def f2():
    time.sleep(0.02)
    return ray.services.get_node_ip_address()

def f3():
    time.sleep(0.02)
    return ray.services.get_node_ip_address()

def run_resource_alloc():
    # force schedule to each of 4 workers
    # funcs = [schedule_to_node(get_ip, i) for i in range(4)]
    funcs = [schedule_to_node(ff, i) for i, ff in enumerate([f0,f1,f2,f3])]
    return ray.get([func.remote() for func in funcs])


while True:
    time.sleep(10)
    print('QUERY WORKERS')
    print(run_resource_alloc())
    # print(ray.get(f2.remote()), ray.get(f3.remote()))
