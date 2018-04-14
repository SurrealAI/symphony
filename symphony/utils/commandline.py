def run(cmd, dry_run=False):
    if dry_run:
        print(cmd)
        return '', '', 0
    else:
        out, err, retcode = run_process(cmd)
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

def run_verbose(cmd,
                print_out=True,
                raise_on_error=False):
    out, err, retcode = run(cmd)
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

