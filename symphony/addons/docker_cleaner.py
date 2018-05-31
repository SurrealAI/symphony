"""
Utilities of cleaning up docker images
"""
import os
import shutil
import re
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

units = ['B', 'K', 'M', 'G']
def format_space(space):
    for unit in units:
        if space > 1024:
            space = space / 1024
        else:
            break
        print('{:.2f}{}'.format(space, unit))

def get_confirmation(prompt):
    while True:
        user_input = input(prompt + "[y/n]: ")
        if user_input.lower() == 'y' or user_input.lower() == 'yes':
            return True
        elif user_input.lower() == 'n' or user_input.lower() == 'no':
            return False

def prune_containers(force):
    if force or get_confirmation("Prune untagged containers?"):
        client = docker.APIClient()
        print('$> docker container prune')
        pruned = client.prune_containers()
        # {'SpaceReclaimed': 34451942, 
        #  'ContainersDeleted': ['a7ebb6...'] (or None)}
        if pruned['ContainersDeleted'] is not None:
            print('Containers deleted:')
            print('\n'.join(pruned['ContainersDeleted']))
            print('Space reclaimed: {}'.format(format_space(pruned['SpaceReclaimed'])))
        else:
            print('No containers to prune')

def prune_images(force):
    if force or get_confirmation("Prune untagged images?"):
        client = docker.APIClient()
        print('$> docker image prune')
        pruned = client.prune_images({'dangling': True})
        if pruned['ImagesDeleted'] is not None:
            for k, v in pruned['ImagesDeleted'].items():
                print('{}: {}'.format(k,v))
            print(format_space(pruned['SpaceReclaimed']))
        else:
            print('No images to prune')

def delete_images(to_delete, force):
    """
    Args:
        to_delete(list): list of docker rmi targets
        force: no confirmation
    """
    print('Images to be deleted:')
    print('\n'.join(to_delete))
    if force or get_confirmation("Confirm delete these images?"):
        client = docker.APIClient()
        for tag in to_delete:
            print('$> docker rmi {}'.format(tag))
            client.remove_image(tag)

def match_res(string, re_exps):
    """
    Returns true if one of the re_exps matches one of the strings
    """
    for re_exp in re_exps:
        if re_exp.match(string):
            return True
        return False

def match_images(re_exp_strs):
    """
    Return all docker images whose tag satisfies one of re_exp_strs
    """
    re_exps = []
    for re_exp_str in re_exp_strs:
        if re_exp_str:
            re_exps.append(re.compile(re_exp_str))
    to_delete = []
    if len(re_exps) > 0:
        client = docker.APIClient()
        for image in client.images():
            if image['RepoTags']:
                for tag in image['RepoTags']:
                    if match_res(tag, re_exps):
                        to_delete.append(tag)
                        break
    return to_delete

def clean_images(re_exp_strs,
                 force=False,
                 force_prune_containers=False,
                 force_prune_images=False):
    prune_containers(force_prune_containers)
    if isinstance(re_exp_strs,str):
        re_exp_strs = [re_exp_strs]
    to_delete = match_images(re_exp_strs)
    if len(to_delete) == 0:
        print('No images found.')
    else:
        delete_images(to_delete, force)
    prune_images(force_prune_images)
