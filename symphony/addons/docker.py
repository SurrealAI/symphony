"""
Utilities of building a docker image by collecting several local directories
"""
from os.path import expanduser
from pathlib import Path
import shutil
import docker


class DockerBuilder:
    """
    Builder for a docker image
    """
    def __init__(self,
                 dockerfile,
                 context_directories,
                 temp_directory,
                 *, verbose=True):
        """
        Args:
        temp_directory(str): temporary directory to create the image in, created if not exist
        dockerfile(str): path to a existing docker file
        context_directories(dict): see self.configure_context()
        verbose(book): report progress of build
        """
        self.temp_directory = Path(expanduser(temp_directory)) / 'symphony_docker_build'
        # Add a folder so that we won't to stupid things like `rm -rf /`
        self.dockerfile = Path(expanduser(dockerfile))
        self.context_directories = {}
        self.configure_context(context_directories)
        self.verbose = verbose

        self.client = docker.from_env()

    def configure_context(self, context_directories):
        """
        Directories specified would be zipped and put into build context
        Args:
        context_directories([{
                    name:(str)
                    path:(str)
                    force_update:(bool)
                    }
                   ]):
        force_update: True to always rezip
                      False to only rezip when the file is missing.
        """
        self.context_directories = {}
        for entry in context_directories:
            entryname = entry['name']
            if entryname in self.context_directories:
                raise ValueError('Name {} is referred to by more than two paths: {}, {}' \
                                    .format(entryname, entry['path'],
                                            self.context_directories[entryname]))
            self.context_directories[entryname] = {
                'name': entryname,
                'path': entry['path'],
                'force_update': entry['force_update'],
            }

    def build(self, tag):
        """
        Excecute build
        """
        self.print("Using temporary build directory {}".format(str(self.temp_directory)))
        self.temp_directory.mkdir(parents=True, exist_ok=True)

        # Copy all temporary files
        for k, v in self.context_directories.items():
            self.retrieve_directory(**v)

        dockerfile = self.dockerfile.open('r')

        response = self.client.build(path=str(self.temp_directory),
                                     decode=True,
                                     fileobj=dockerfile,
                                     tag=tag)
        print(response)

    def retrieve_directory(self, name, path, force_update):
        """
        Copy a directory to temp_file_path
        Args:
            name(str): put files to self.temp_directory / name
            path(str): the directory to zip
            force_update(bool): True: always overwrite existing files in the build directory
                                False: only overwrite if files in the build directory don't exist
        """
        target_path = self.temp_directory / name
        if target_path.exists():
            if force_update:
                self.print("removing cached files at {}".format(target_path))
                shutil.rmtree(target_path)
            else:
                self.print("Using cached files at {}".format(target_path))
                return
        source = path
        target = str(target_path)
        self.print('cp -r {} {}'.format(source, target))
        shutil.copytree(source, target)
        return

    def print(self, *args, **kwargs):
        """
        print depending on verbose settings
        """
        if self.verbose:
            print(*args, **kwargs)
