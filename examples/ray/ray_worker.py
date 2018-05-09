import sys
import time
import subprocess


success = False

while not success:
    proc = subprocess.run(
        'ray start --redis-address=$SYMPH_REDIS_SERVER_ADDR',
        shell=True
    )
    success = proc.returncode == 0
    if not success:
        print('RAY START FAILURE exit code', proc.returncode)
        print('retry ...')
        time.sleep(3)

print('='*30, 'WORKER STARTED', sys.argv[1], '='*30)

time.sleep(10000)
