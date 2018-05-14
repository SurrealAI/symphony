"""
Get env variables that are defined at symphony cluster launch time.
"""
import os
import json


RAY_MASTER_SERVICE = 'ray-master-redis'  # for satellites to connect
RAY_ZMQ_SYNC = 'ray-zmq-sync'  # sync cluser start-up to a particular order


def ray_master_redis_port():
    """
    Use in master driver script.
    Make sure the master process in symphony binds to 'ray_master_redis'
    and satellite processes connects to 'ray_master_redis'
    """
    return int(os.environ['SYMPH_RAY_MASTER_REDIS_PORT'])


def ray_master_redis_addr():
    """
    Use on satellite nodes.
    Make sure the master process in symphony binds to 'ray_master_redis'
    and satellite processes connects to 'ray_master_redis'
    """
    return os.environ['SYMPH_RAY_MASTER_REDIS_ADDR']


def ray_zmq_port():
    """
    Use in master driver script.
    ZmqServer on master node should bind to tcp://*:<port>
    """
    return int(os.environ['SYMPH_RAY_ZMQ_SYNC_PORT'])


def ray_zmq_addr():
    """
    Use on satellite nodes.
    Satellite ZmqClient should all connect to this addr
    """
    return os.environ['SYMPH_RAY_ZMQ_SYNC_ADDR']


def ray_resources():
    return json.loads(os.environ['SYMPH_RAY_RESOURCES'])


def ray_id():
    return os.environ['SYMPH_RAY_ID']


def ray_num_satellites():
    "useful in master only"
    return int(os.environ['SYMPH_RAY_NUM_SATELLITES'])


def generate_env_dict(id, resources=None, other_envs=None):
    """
    Generate env dict for ray nodes.
    Should be used in symphony launch script. Pass to KubeProcess constructor.

    Args:
        resources: dict of custom resources, None for empty
            include {"gpu": 4} if you want to use GPU on the satellite node
        other_envs: extra env vars to be included
    """
    if resources is None:
        resources = {}
    else:
        assert isinstance(resources, dict)
    if other_envs is None:
        other_envs = {}
    else:
        assert isinstance(other_envs, dict)
    envs = {
        'SYMPH_RAY_ID': str(id),
        'SYMPH_RAY_RESOURCES': json.dumps(resources)
    }
    others = {k: str(v) for k, v in other_envs.items()}
    envs.update(others)
    return envs

