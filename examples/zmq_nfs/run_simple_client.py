import os
import time
from caraml.zmq import *
from nfs_settings import *


client = ZmqClient(
    host=os.environ['SYMPH_EXAMPLE_HOST'],
    port=os.environ['SYMPH_EXAMPLE_PORT'],
    serializer='json',
    deserializer='json'
)
s = client.socket
print_and_write('client.txt', s.address, s.host, s.port)

msg = {'counter': 10, 'scream': 'hello'}

for i in range(20):
    time.sleep(.5)
    msg = client.request(msg)
    print_and_write('client.txt', 'client request', i)

while True:  # block
    time.sleep(100000)
