# docker push destination URL
UPSTREAM_URL = 'us.gcr.io/jimfan2018-208323/symphony-demo-zmq-nfs'
NFS_SERVER = 'surreal-nfs-vm'  # NFS server VM name on GCE
NFS_PATH_ON_SERVER = '/data'  # path on the NFS server VM
NFS_MOUNT_PATH = '/fs'  # path accessible to the pods
DEMO_FOLDER = '/fs/demo_zmq'


import os
def print_and_write(file_name, *args):
    assert os.path.exists(NFS_MOUNT_PATH), \
        'NFS mount path `{}` not found'.format(NFS_MOUNT_PATH)
    print(*args)
    file_name = os.path.join(DEMO_FOLDER, file_name)
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    with open(file_name, 'a') as fp:
        print(*args, file=fp)
