import sys
import shlex
import time
import subprocess
from benedict import dump_json_str

RANK = int(sys.argv[1])

success = False
trials = 0

resources = {'tag{}'.format(RANK): 1000000}

while not success:
    proc = subprocess.run(
        'ray start --redis-address=$SYMPH_REDIS_SERVER_ADDR --resources={}'
        .format(shlex.quote(dump_json_str(resources))),
        shell=True
    )
    exitcode = proc.returncode
    success = exitcode == 0
    if not success:
        print('Trial #{}: ray init failure exit code {}'.format(trials, exitcode))
        print('retry ...')
        time.sleep(3)
    trials += 1

print('='*30, 'WORKER STARTED', RANK, '='*30)

time.sleep(10000)
