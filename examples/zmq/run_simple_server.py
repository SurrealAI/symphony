from caraml.zmq import *
import os
import json


def handler(msg):
    print('handling', msg)
    msg['counter'] += 1
    msg['scream'] += 'a'
    return msg

port = os.environ['SYMPH_EXAMPLE_PORT']
listen_addr = 'tcp://*:{}'.format(port)

server = ZmqServer(
    address=listen_addr,
    serializer='json',
    deserializer='json'
)
print('Server initialized')
s = server.socket
print(s.address, s.host, s.port)
print('Starting event loop')
server.start_event_loop(handler, blocking=True)
