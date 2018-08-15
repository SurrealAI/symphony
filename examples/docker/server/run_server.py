import os
from caraml.zmq import *


def handler(msg):
    print('handling ', msg, flush=True)
    msg['counter'] += 1
    msg['scream'] += 'a'
    return msg


def main():
    port = os.environ['TEST_PORT']
    listen_addr = 'tcp://*:{}'.format(port)
    server = ZmqServer(
        address=listen_addr,
        serializer='json',
        deserializer='json'
    )
    print('Server initialized', flush=True)
    s = server.socket
    print(s.address, s.host, s.port, flush=True)
    print('Starting event loop', flush=True)
    server.start_event_loop(handler, blocking=True)


if __name__ == '__main__':
    print('Running SERVER', flush=True)
    main()
