from symphony.zmq import *
import os
import time
import json


client = ZmqClient(
    host=os.environ['SYMPH_EXAMPLE_HOST'], port=os.environ['SYMPH_EXAMPLE_PORT'],
    serializer='json',
    deserializer='json'
)
s = client.socket
print(s.address, s.host, s.port)

msg = {'counter': 10, 'scream': 'hello'}

for _ in range(20):
    time.sleep(1)
    msg = client.request(msg)

while True:  # block
    time.sleep(100000)
