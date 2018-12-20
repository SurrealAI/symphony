import time
import os
from pprint import pprint
from symphony.subproc import SubprocManager


manager = SubprocManager(
    stdout_mode='print',
    stderr_mode='print',
    log_dir='mylogs'
)


p1 = manager.launch('dummy1', 'python dummy.py 10 d1', env={'DUMMY': 'first'})
p2 = manager.launch('dummy2', 'python dummy.py 8 d2', env={'DUMMY': 'second'})
# put "throw" in command line arg to simulate an exception
p3 = manager.launch('dummy3', 'python dummy.py 6 hello', env={'DUMMY': 'third'})

print(p1.pid, p2.pid, p3.pid)

# time.sleep(3)
# print('killing ...')
# manager.kill_all()

print('Main PID', os.getpid())
manager.join(kill_on_error=True)
pprint(manager.poll_all())
