from symphony.kube import *
from .symph_envs import ray_env_dict, RAY_MASTER_SERVICE


class RayKubeCluster(KubeCluster):
    def new_experiment(self, *args, **kwargs):
        return RayKubeExperimentSpec(*args, **kwargs)


class RayKubeExperimentSpec(KubeExperimentSpec):
    def new_master_process(self, container_image=None,
                           command=None,
                           args=None,
                           resources=None,
                           env=None):
        """
        Create a process of name "master" and SYMPH_RAY_ID = "master"
        binds to RAY_MASTER_DNS_ID
        mounts shared memory at /dev/shm

        Args:
            container_image:
            command:
            args:
            resources: dict of Ray custom resources
            env:
        """
        proc = self.new_process(
            name='master',
            container_image=container_image,
            command=command,
            args=args,
            env=ray_env_dict('master', resources=resources, other_envs=env)
        )
        proc.binds(RAY_MASTER_SERVICE)
        proc.mount_shared_memory()
        return proc

    def new_satellite_process(self, id,
                              container_image=None,
                              command=None,
                              args=None,
                              resources=None,
                              env=None):
        """
        Create a process of name "sat{id}" and SYMPH_RAY_ID = "{id}"
        connects to RAY_MASTER_DNS_ID
        mounts shared memory at /dev/shm

        Args:
            id: satellite ID
            container_image:
            command:
            args:
            resources: dict of Ray custom resources
            env:
        """
        proc = self.new_process(
            name='sat{}'.format(id),
            container_image=container_image,
            command=command,
            args=args,
            env=ray_env_dict(id, resources=resources, other_envs=env)
        )
        proc.connects(RAY_MASTER_SERVICE)
        proc.mount_shared_memory()
        return proc
