from symphony.zmq import *
import time
import json


client = ZmqClient(
    'localhost', 7555,
    serializer=json.dumps,
    deserializer=json.loads
)

msg = {'counter': 10, 'scream': 'hello'}

for _ in range(10):
    time.sleep(1)
    msg = client.request(msg)
