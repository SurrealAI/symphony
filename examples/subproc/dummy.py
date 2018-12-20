"""
Used for testing SubprocManager
"""
import os
import sys
import time

assert 'DUMMY' in os.environ
ENV = os.environ['DUMMY']

n = int(sys.argv[1])
for i in range(n):
    time.sleep(1)
    print(i, 'env=', ENV, 'args=', *sys.argv[2:])
    print('err', i, 'env=', ENV, 'args=', *sys.argv[2:],
          file=sys.stderr)
    if 'throw' in sys.argv and i >= n // 2:
        raise ValueError('{} {}', i, ENV)

print('DONE', *sys.argv[2:])