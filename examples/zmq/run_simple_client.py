from symphony.zmq import *
import time
import json


client = ZmqClient(
    host='localhost', port=7555,
    serializer='json',
    deserializer='json'
)
s = client.socket
print(s.address, s.host, s.port)

msg = {'counter': 10, 'scream': 'hello'}

for _ in range(10):
    time.sleep(1)
    msg = client.request(msg)
