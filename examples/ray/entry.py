#!/usr/bin/env python
"""
ENV variables
- mujoco_key_text: plain text environment value
- repo_surreal: /mylibs/surreal/surreal
- repo_tensorplex

"""
import os
import sys
import shlex
import argparse
import shutil
import glob
import errno

parser = argparse.ArgumentParser()
parser.add_argument('--cmd', type=str, nargs='+', help='run arbitrary command')
parser.add_argument('--bash', type=str, default='', help='bash shell script')
parser.add_argument('-i', '--interact', action='store_true', help='start interactive bash')
parser.add_argument('--py', type=str, default='', help='python script')

args = parser.parse_args()


def f_copy(fsrc, fdst):
    """
    If exist, remove. Supports both dir and file. Supports glob wildcard.
    """
    for f in glob.glob(fsrc):
        try:
            shutil.copytree(f, fdst)
        except OSError as e:
            if e.errno == errno.ENOTDIR:
                shutil.copy(f, fdst)


def init():
    """
    Two ways to pass the mujoco key into the docker container:
    1. put the mjkey.txt textual string into environment variable `mujoco_key_text`
    2. mount the mjkey.txt file in /mujoco/
        docker -ti -v $HOME/.mujoco:/mujoco <docker-image> <...run commands...>
    """
    os.system('/usr/bin/Xorg -noreset +extension GLX '
              '+extension RANDR +extension RENDER -logfile /etc/fakeX/10.log '
              '-config /etc/fakeX/xorg.conf :10 > /dev/null 2>&1 &')
    mujoco_key = os.environ.get('mujoco_key_text', '')
    os.system('mkdir -p /root/.mujoco')
    if mujoco_key:
        with open('/root/.mujoco/mjkey.txt', 'w') as fp:
            fp.write(mujoco_key)
    elif os.path.exists('/mujoco/mjkey.txt'):
        f_copy('/mujoco/mjkey.txt', '/root/.mujoco')
    else:
        print('WARNING: missing Mujoco `mjkey.txt`')


# init()


if args.interact:
    os.system('bash')
elif args.cmd:
    if len(args.cmd) == 1:
        os.system(args.cmd[0])
    else:  # docker run
        os.system(' '.join(map(shlex.quote, args.cmd)))
elif args.py:
    assert args.py.endswith('.py')
    os.system('python -u ' + args.py)
elif args.bash:
    os.system('/bin/bash ' + args.bash)
else:
    print('No args given to /mylibs/entry.py')
