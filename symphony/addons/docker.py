"""
Utilities of building a docker image by collecting several local directories
"""
import tarfile
from os.path import expanduser
from pathlib import Path


class DockerBuilder:
    """
    Builder for a docker image
    """
    def __init__(self,
                 dockerfile,
                 needed_directories,
                 temp_directory,
                 *, verbose=True):
        """
        Args:
        temp_directory(str): temporary directory to create the image in, created if not exist
        dockerfile(str): path to a existing docker file
        needed_directories([{
                            name:(str)
                            path:(str)
                            force_update:(bool)
                            }
                           ]): Directories under these paths will
                               be zipped and put into build context
        force_updates(str)
        verbose(book): report progress of build
        """
        self.temp_directory = Path(expanduser(temp_directory))
        self.dockerfile = Path(expanduser(dockerfile))
        self.needed_directories = {}
        for entry in needed_directories:
            entryname = entry['name']
            if entryname in self.needed_directories:
                raise ValueError('Name {} is referred to by more than two paths: {}, {}' \
                                    .format(entryname, entry['path'],
                                            self.needed_directories[entryname]))
            self.needed_directories[entryname] = {
                'name': entryname,
                'path': entry['path'],
                'force_update': entry['force_update'],
            }
        self.verbose = verbose

    def build(self, image_name):
        """
        Excecute build
        """
        if self.verbose:
            print("Using temporary build directory {}".format(str(self.temp_directory)))
        self.temp_directory.mkdir(parents=True, exist_ok=True)

        for k, v in self.needed_directories.items():
            self.retrieve_directory(**v)
        # Tar all temporary files
        #

    def retrieve_directory(self, name, path, force_update):
        """
        Zip a directory to temp_file_path
        Args:
            name(str): put files to self.temp_directory / name
            path(str): the directory to zip
            force_update(bool): True: always overwrite existing files in the build directory
                                False: only overwrite if files in the build directory don't exist
        """
        if self.verbose:
            print('Zipping directory at {}'.format(path))
            



