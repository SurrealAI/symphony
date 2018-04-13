from symphony import AddressBook
from symphony.address import AddressDeclarationError
import os
import json

"""
    The addressBook helps to manage port numbers across different processes
"""

os.environ['SYMPHONY_ROLE'] = 'testing'
os.environ['SYMPHONY_AB_DATA'] = json.dumps({
    'services': {
        'backend_1' :{
            'provider_host': 'localhost',
            'provider_port': 7003,
            'requester_host': 'localhost',
            'requester_port': 7004,
        },
        'backend_2' :{
            'provider_host': 'hello',
            'provider_port': 7005,
            # 'requester_host': 'localhost'
            # 'requester_port': '7003',
        },
        'backend_3': {
            # 'provider_host': 'localhost',
            # 'provider_port': '7003',
            'requester_host': 'world',
            'requester_port': 8005,
        },
    }})

### Inside the process that is running
from symphony import AddressBook

ab = AddressBook(verbose=False)

host1, port1 = ab.request('backend_1')
assert host1 == 'localhost', port1 == 7003
host2, port2 = ab.provide('backend_1')
assert host2 == 'localhost', port2 == 7004
host3, port3 = ab.provide('backend_2')
assert host3 == 'hello', port3 == 7005
host4, port4 = ab.request('backend_3')
assert host4 == 'world', port4 == 8005
raised = False
try:
    host5, port5 = ab.request('backend_2')
except AddressDeclarationError as e:
    print(e)
    raised = True
assert raised
raised = False
try:
    host6, port6 = ab.provide('backend_3')
except AddressDeclarationError as e:
    print(e)
    raised = True
assert raised
print('passed')