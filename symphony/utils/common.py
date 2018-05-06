import re
import sys
import collections
from io import StringIO
from collections import OrderedDict
import yaml



def merge_dict(d, u):
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            d[k] = merge_dict(d.get(k, type(v)()), v)
        elif isinstance(v, list):
            d[k] = d.get(k, []) + v
        else:
            d[k] = v
    return d

def dump_yml(di):
    stream = StringIO()
    yaml.dump(
        di,
        stream,
        default_flow_style=False,
        indent=2
    )
    return stream.getvalue()

def strip_repository_name(git_repo_url):
    """
        Strips the input and returns the text between rightmost '/' and '.git'
    """
    output = git_repo_url
    last_slash = output.rfind('/')
    if last_slash != -1:
        output = output[last_slash + 1:]
    dot_git = output.rfind('.git')
    if dot_git != -1:
        output = output[:dot_git]
    return output.lower()

def print_err(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)

def sanitize_name_kubernetes(name, verbose=True):
    """
        Transform name to lowercase, replace '.', ' ' and '_' to '-'
    Args:
        name: the name to be sanitized
        verbose: print warning message when the name is replaced
    """
    sanitized_name = name
    sanitized_name = sanitized_name.lower()
    sanitized_name = sanitized_name.replace(' ', '-')
    sanitized_name = sanitized_name.replace('_', '-')
    sanitized_name = sanitized_name.replace('.', '-')
    if sanitized_name != name and verbose:
        print('[Warning] Name {} is replaced by {}.'.format(name, sanitized_name))
    check_valid_dns(sanitized_name)
    return sanitized_name

_DNS_RE = re.compile('^[a-z0-9]([-a-z0-9]*[a-z0-9])?$')

def check_valid_dns(name):
    """
    experiment name is used as namespace, which must conform to DNS format
    """
    if not _DNS_RE.match(name):
        raise ValueError(name + ' must be a valid DNS name with only lower-case '
                         'letters, 0-9 and hyphen. No underscore or dot allowed.')

def is_sequence(obj):
    """
    Returns:
      True if the sequence is a collections.Sequence and not a string.
    """
    return (isinstance(obj, collections.Sequence)
            and not isinstance(obj, str))

def deduplicate_with_order(seq):
    """
    https://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-in-whilst-preserving-order
    deduplicate list while preserving order
    """
    return list(OrderedDict.fromkeys(seq))
