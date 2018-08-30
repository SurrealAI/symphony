import os
import json
from caraml.zmq import *
from nfs_settings import *


def handler(msg):
    print_and_write('server.txt', 'handling', msg)
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
print_and_write('server.txt', 'Server initialized')
s = server.socket
print_and_write('server.txt', s.address, s.host, s.port)
print_and_write('server.txt', 'Starting event loop')
server.start_event_loop(handler, blocking=True)
