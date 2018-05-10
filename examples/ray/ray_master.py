import os
import ray
import time

port = os.environ['SYMPH_REDIS_SERVER_PORT']
os.system('ray start --head --redis-port={}'.format(port))
time.sleep(2)

ray.init(redis_address='localhost:'+port)

@ray.remote
def f():
    time.sleep(0.02)
    return ray.services.get_node_ip_address()

print('SUCCESSFULLY STARTED', '='*50)

def get_ips():
    # Get a list of the IP addresses of the nodes that have joined the cluster.
    return list(set(ray.get([f.remote() for _ in range(1000)])))


while True:
    time.sleep(10)
    print('QUERY WORKERS')
    print(get_ips())
