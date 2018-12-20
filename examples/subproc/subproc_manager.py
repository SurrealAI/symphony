import time
from pprint import pprint
from symphony.subproc import SubprocManager


manager = SubprocManager(
    stdout_mode='print',
    stderr_mode='print',
    log_dir='mylogs'
)


manager.launch('dummy1', 'python dummy.py 10 d1', env={'DUMMY': 'first'})
manager.launch('dummy2', 'python dummy.py 8 d2', env={'DUMMY': 'second'})
manager.launch('dummy3', 'python dummy.py 6 d3', env={'DUMMY': 'third'})


# time.sleep(3)
# print('killing ...')
# manager.kill_all()

manager.join(kill_on_error=True)
pprint(manager.poll_all())
