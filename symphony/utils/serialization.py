"""
Serializes numpy and JSON-like objects
"""
import pickle
import base64
import hashlib
import json
import marshal
import pyarrow


def pa_serialize(obj):
    return pyarrow.serialize(obj).to_buffer()


def pa_deserialize(binary):
    return pyarrow.deserialize(binary)


def bytes2str(bytestring):
    if isinstance(bytestring, str):
        return bytestring
    else:
        return bytestring.decode('UTF-8')


def str2bytes(string):
    if isinstance(string, bytes):
        return string
    else:
        return string.encode('UTF-8')


_SERIALIZERS = {
    'str': str2bytes,
    'pickle': pickle.dumps,
    'marshal': marshal.dumps,
    'json': json.dumps,
    'pyarrow': pa_serialize,
}

_DESERIALIZERS = {
    'str': bytes2str,
    'pickle': pickle.loads,
    'marshal': marshal.loads,
    'json': json.loads,
    'pyarrow': pa_deserialize,
}


def get_serializer(serializer):
    """
    Args:
        serializer: one of the following
            - pre-set method (str)
            - callable
            - None: no-op
    """
    if serializer is None:
        return lambda x: x
    elif isinstance(serializer, str):
        # pre-set serializers
        serializer = serializer.lower()
        return _SERIALIZERS[serializer]
    elif callable(serializer):
        return serializer
    else:
        raise ValueError('serializer must be either a callable or one of {}'
                         .format(list(_SERIALIZERS.keys())))


def get_deserializer(deserializer):
    """
    Args:
        deserializer: one of the following
            - pre-set method (str)
            - callable
            - None: no-op
    """
    if deserializer is None:
        return lambda x: x
    elif isinstance(deserializer, str):
        # pre-set serializers
        deserializer = deserializer.lower()
        return _DESERIALIZERS[deserializer]
    elif callable(deserializer):
        return deserializer
    else:
        raise ValueError('deserializer must be either a callable or one of {}'
                         .format(list(_DESERIALIZERS.keys())))


def string_hash(s):
    assert isinstance(s, str)
    return binary_hash(s.encode('utf-8'))


def binary_hash(binary):
    """
    Low collision hash of any binary string
    For designating the 16-char object key in Redis.
    Runs at 200 mu-second per hash on Macbook pro.
    Only contains characters from [a-z][A-Z]+_
    """
    s = hashlib.md5(binary).digest()
    s = base64.b64encode(s)[:16]
    s = s.decode('utf-8')
    # return s.replace('/','_')
    return s


def pyobj_hash(obj, serializer):
    serializer = get_serializer(serializer)
    return binary_hash(serializer(obj))
