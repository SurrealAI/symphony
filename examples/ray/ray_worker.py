import sys
import time
import subprocess


success = False
trials = 0

while not success:
    proc = subprocess.run(
        'ray start --redis-address=$SYMPH_REDIS_SERVER_ADDR',
        shell=True
    )
    exitcode = proc.returncode
    success = exitcode == 0
    if not success:
        print('Trial #{}: ray init failure exit code {}'.format(trials, exitcode))
        print('retry ...')
        time.sleep(3)
    trials += 1

print('='*30, 'WORKER STARTED', sys.argv[1], '='*30)

time.sleep(10000)
