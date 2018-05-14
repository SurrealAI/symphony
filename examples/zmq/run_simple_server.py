from symphony.zmq import *
import json


def handler(msg):
    print('handling', msg)
    msg['counter'] += 1
    msg['scream'] += 'a'
    return msg


server = ZmqServer(
    '*:7555',
    serializer=json.dumps,
    deserializer=json.loads
)
s = server.socket
print(s.address, s.host, s.port)
server.start_event_loop(handler, blocking=True)
