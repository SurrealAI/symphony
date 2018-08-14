import os
import json
import sys
import time

from symphony.zmq import *


def main():
    host = os.environ['TEST_HOST']
    port = os.environ['TEST_PORT']
    print('Host: {}, Port: {}'.format(host, port), flush=True)
    client = ZmqClient(
        host=host, port=port,
        serializer='json',
        deserializer='json'
    )
    s = client.socket
    print('Created ZmqClient:', flush=True)
    print(s.address, s.host, s.port, flush=True)

    msg = {'counter': 10, 'scream': 'hello'}

    for _ in range(1000):
        time.sleep(5)
        msg = client.request(msg)

    while True:  # block
        time.sleep(100000)


if __name__ == '__main__':
    print('Running client', flush=True)
    main()
