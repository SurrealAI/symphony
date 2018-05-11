"""
Utilities of building a docker image by collecting several local directories
"""
import os
import shutil
import re
from os.path import expanduser
from pathlib import Path
import docker
from symphony.utils.common import print_err


class DockerRecordMaster:
    """
    Manages docker information, returns docker builder
    """
    def __init__(self, configs=None):
        self.settings = {}
        if configs is not None:
            self.load_all(configs)

    def load_all(self, li):
        """
        load all configs in list li
        """
        for di in li:
            self.add_config(di)

    def add_config(self, di):
        """
        Add a setting to the storage
        """
        name = di['name']
        if name in self.settings:
            print_err('[Warning] Overwriting docker build setting for {}'.format(name))
        self.settings[name] = DockerBuilder.format_docker_build_settings(di)

    def get(self, name):
        """
        Return a DockerBuilder instance under name @name
        """
        return DockerBuilder(**(self.settings[name]))


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

        self.client = docker.APIClient()

    @classmethod
    def format_docker_build_settings(cls, di):
        """
        Formats di so it can intialize a DockerBuilderInstance
        """
        if 'name' not in di:
            raise ValueError('[Error] Every build setting must have a name')
        name = di['name']
        if 'temp_directory' not in di:
            print_err('[Warning] Setting build directory of {} to /tmp/symphony'.format(name))
            di['temp_directory'] = '/tmp/symphony'
        if 'context_directories' not in di:
            print_err('[Warning] {} has no dependent files'.format(name))
            di['context_directories'] = []
        if 'dockerfile' not in di:
            raise ValueError('[Error] Must provide a dockerfile for build setting {}'.format(name))
        config = {
            'temp_directory': str(di['temp_directory']),
            'context_directories': list(di['context_directories']),
            'dockerfile': str(di['dockerfile']),
        }
        if 'verbose' in di:
            config['verbose'] = di['verbose']
        return config

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
                      Default True
        """
        self.context_directories = {}
        for entry in context_directories:
            entryname = entry['name']
            if entryname in self.context_directories:
                raise ValueError('[Error] Name {} is referred to by more than two paths: {}, {}' \
                                    .format(entryname, entry['path'],
                                            self.context_directories[entryname]))
            if 'force_update' not in entry:
                entry['force_update'] = True
            self.context_directories[entryname] = {
                'name': entryname,
                'path': expanduser(entry['path']),
                'force_update': entry['force_update'],
            }

    def build(self, tag=None):
        """
        Excecute build
        Returns image id or None if build failed
        """
        self.print("[Info] Using temporary build directory {}".format(str(self.temp_directory)))
        self.temp_directory.mkdir(parents=True, exist_ok=True)

        # Copy dockerfile
        self.copy_dockerfile()
        # Copy all temporary files
        for k, v in self.context_directories.items():
            self.retrieve_directory(**v)

        print('[Info] Building')
        response = self.client.build(path=str(self.temp_directory),
                                     decode=True, tag=tag)
        last_event = None
        for line_parsed in response:
            self.output_docker_res(line_parsed)
            last_event = line_parsed

        if last_event is not None and 'stream' in last_event:
            match = re.search(r'Successfully built ([0-9a-f]+)',
                              last_event.get('stream', ''))
            if match:
                image_id = match.group(1)
                self.img = image_id

    def output_docker_res(self, line_parsed):
        """
        Parse docker output
        """
        if 'stream' in line_parsed:
            self.print(line_parsed['stream'], end='', flush=True)
        elif 'error' in line_parsed:
            self.print(line_parsed['error'])
        else:
            self.print(line_parsed)

    def push(self, repository, tag=None):
        """
        docker push
        """
        if self.img is None:
            raise ValueError("[Error] Image not build, cannot push")

        # Docker api is bad
        # res = self.client.push(repository, tag=tag, stream=True, decode=True)
        tag_name = self.tag_name(repository, tag)
        os.system(' '.join(['docker', 'push', tag_name]))

        # for line in res:
        #     self.output_docker_res(line)

    def tag(self, repository, tag=None, force=False):
        """
        docker tag
        """
        if self.img is None:
            raise ValueError("[Error] Image not build, cannot tag")

        success = self.client.tag(self.img, repository, tag, force)
        tag_name = self.tag_name(repository, tag)

        if success:
            self.print('[Info] Successfully tagged {} with {}'.format(self.img, tag_name))
        else:
            raise RuntimeError('[Error] Tag {} failed'.format(tag_name))

    def tag_name(self, repository, tag=None):
        """
        Returns repository or repository:tag
        """
        if tag is None:
            return repository
        else:
            return '{}:{}'.format(repository, tag)

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
                self.print("[Info] Removing cached files at {}".format(target_path))
                shutil.rmtree(str(target_path))
            else:
                self.print("[Info] Using cached files at {}".format(target_path))
                return
        source = path
        target = str(target_path)
        self.print('cp -r {} {}'.format(source, target))
        shutil.copytree(source, target)
        return

    def copy_dockerfile(self):
        """
        copy dockerfile to temp directory
        """
        dockerfile_path = (self.temp_directory / 'Dockerfile')
        self.print('[Info] Copying dockerfile from {} to {}' \
                   .format(str(self.dockerfile), str(dockerfile_path)))
        with dockerfile_path.open('w') as f:
            with self.dockerfile.open('r') as f_in:
                for line in f_in:
                    f.write(line)


    def print(self, *args, **kwargs):
        """
        print depending on verbose settings
        """
        if self.verbose:
            print(*args, **kwargs)
