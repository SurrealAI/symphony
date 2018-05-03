import subprocess as pc
import os
from symphony.utils.common import print_err


def run_process(cmd, stdin=''):
    # if isinstance(cmd, str):  # useful for shell=False
    #     cmd = shlex.split(cmd.strip())
    proc = pc.Popen(cmd, stdin=pc.PIPE, stdout=pc.PIPE, stderr=pc.PIPE, shell=True)
    out, err = proc.communicate(stdin.encode())
    return out.decode('utf-8'), err.decode('utf-8'), proc.returncode

def run(cmd, dry_run=False, stdin=''):
    if dry_run:
        print(cmd)
        return '', '', 0
    else:
        out, err, retcode = run_process(cmd, stdin)
        if 'could not find default credentials' in err:
            print("Please try `gcloud container clusters get-credentials mycluster` "
                  "to fix credential error")
        return out.strip(), err.strip(), retcode

def run_raw(cmd, print_cmd=False, dry_run=False):
    """
    Raw os.system calls

    Returns:
        error code
    """
    if dry_run:
        print(cmd)
    else:
        if print_cmd:
            print(cmd)
        return os.system(cmd)

def _print_err_return(out, err, retcode):
    print_err('error code:', retcode)
    print_err('*' * 20, 'stderr', '*' * 20)
    print_err(err)
    print_err('*' * 20, 'stdout', '*' * 20)
    print_err(out)
    print_err('*' * 46)

def run_verbose(cmd,print_out=True,raise_on_error=False,dry_run=False,stdin=''):
    out, err, retcode = run(cmd, dry_run=dry_run, stdin=stdin)
    if retcode != 0:
        _print_err_return(out, err, retcode)
        msg = 'Command `{}` fails'.format(cmd)
        if raise_on_error:
            raise RuntimeError(msg)
        else:
            print_err(msg)
    elif out and print_out:
        print(out)
    return out, err, retcode

