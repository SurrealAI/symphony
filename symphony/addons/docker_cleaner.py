"""
Utilities of cleaning up docker images
"""
import os
import shutil
import re
import fnmatch
from os.path import expanduser
from pathlib import Path
import docker
import nanolog as nl


_log = nl.Logger.create_logger(
    'dockercleaner',
    level=nl.INFO,
    time_format='HMS',
    show_level=True,
    stream='stderr'
)


def _format_space(space):
    units = ['B', 'K', 'M', 'G']
    for unit in units:
        if space > 1024:
            space = space / 1024
        else:
            break
        print('{:.2f}{}'.format(space, unit))


def _get_confirmation(prompt):
    while True:
        user_input = input(prompt + "[y/n]: ")
        if user_input.lower() == 'y' or user_input.lower() == 'yes':
            return True
        elif user_input.lower() == 'n' or user_input.lower() == 'no':
            return False


def _prune_containers(force):
    print()
    if force or _get_confirmation("Prune untagged containers?"):
        client = docker.APIClient()
        print('$> docker container prune')
        pruned = client.prune_containers()
        # {'SpaceReclaimed': 34451942, 
        #  'ContainersDeleted': ['a7ebb6...'] (or None)}
        if pruned['ContainersDeleted'] is not None:
            print('Containers deleted:')
            print('\n'.join(pruned['ContainersDeleted']))
            print('Space reclaimed: {}'.format(_format_space(pruned['SpaceReclaimed'])))
        else:
            print('No containers to prune')


def _prune_images(force):
    print()
    if force or _get_confirmation("Prune untagged images?"):
        client = docker.APIClient()
        print('$> docker image prune')
        pruned = client.prune_images({'dangling': True})
        if pruned['ImagesDeleted'] is not None:
            for pruned_image in pruned['ImagesDeleted']:
                for k, v in pruned_image.items():
                    print('{}: {}'.format(k,v))
            print(_format_space(pruned['SpaceReclaimed']))
        else:
            print('No images to prune')


def _delete_images(to_delete, force):
    """
    Args:
        to_delete(list): list of docker rmi targets
        force: no confirmation
    """
    print()
    print('Images to be deleted:')
    print('\n'.join(to_delete))
    if force or _get_confirmation("Confirm delete these images?"):
        client = docker.APIClient()
        for tag in to_delete:
            print('$> docker rmi {}'.format(tag))
            client.remove_image(tag)


def _match_res(string, re_exps):
    """
    Returns true if one of the re_exps matches one of the strings
    """
    for re_exp in re_exps:
        if re_exp.match(string):
            return True
        return False


def _match_images(re_exps):
    """
    Return all docker images whose tag satisfies one of re_exp_strs
    """
    to_delete = []
    if len(re_exps) > 0:
        client = docker.APIClient()
        for image in client.images():
            if image['RepoTags']:
                for tag in image['RepoTags']:
                    if _match_res(tag, re_exps):
                        to_delete.append(tag)
                        break
    return to_delete


def _clean_images_re(re_exp_strs,
                     force=False,
                     force_prune_containers=False,
                     force_prune_images=False):
    if isinstance(re_exp_strs,str):
        re_exp_strs = [re_exp_strs]
    re_exps = [re.compile(s) for s in re_exp_strs]
    _prune_containers(force_prune_containers)
    to_delete = _match_images(re_exps)
    if len(to_delete) == 0:
        print('No images found.')
    else:
        _delete_images(to_delete, force)
    _prune_images(force_prune_images)


def clean_images(fnmatch_strs,
                 force=False,
                 force_prune_containers=False,
                 force_prune_images=False):
    """
    Uses fnmatch format to find repo:tag pairs
    """
    if isinstance(fnmatch_strs,str):
        fnmatch_strs = [fnmatch_strs]
    re_exps = [fnmatch.translate(x) for x in fnmatch_strs]
    _clean_images_re(re_exps, force, force_prune_containers, force_prune_images)
