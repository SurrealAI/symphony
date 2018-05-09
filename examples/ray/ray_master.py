import os
import ray
import time

port = os.environ['SYMPH_REDIS_PORT']
os.system('ray start --head --redis-port={}'.format(port))
time.sleep(2)

ray.init(redis_address='localhost:'+port)

@ray.remote
def f():
    time.sleep(0.05)
    return ray.services.get_node_ip_address()


# Get a list of the IP addresses of the nodes that have joined the cluster.
all_ips = set(ray.get([f.remote() for _ in range(1000)]))
print(list(all_ips))

