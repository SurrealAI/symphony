"""
Utilities of building a docker image by collecting several local directories
"""
import os
import shutil
import re
from os.path import expanduser
from pathlib import Path
import docker
import nanolog as nl


_log = nl.Logger.create_logger(
    'dockerbuilder',
    level=nl.INFO,
    time_format='HMS',
    show_level=True,
    stream='stderr'
)

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
        self.img = None
        if not verbose:
            _log.set_level(nl.WARN)
        self.client = docker.APIClient()

    @classmethod
    def from_dict(cls, di):
        """
        Formats di and intializes a DockerBuilderInstance
        """
        if 'dockerfile' not in di:
            raise ValueError('Must provide a dockerfile for build setting')
        if 'temp_directory' not in di:
            _log.warn('Setting build directory to default: /tmp/symphony')
            di['temp_directory'] = '/tmp/symphony'
        if 'context_directories' not in di:
            _log.warn('Build setting has no dependent files')
            di['context_directories'] = []
        config = {
            'temp_directory': str(di['temp_directory']),
            'context_directories': list(di['context_directories']),
            'dockerfile': str(di['dockerfile']),
        }
        if 'verbose' in di:
            config['verbose'] = di['verbose']
        return DockerBuilder(**config)

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
                raise ValueError(
                    'Name {} is referred to by more than two paths: {}, {}'
                    .format(entryname, entry['path'], self.context_directories[entryname])
                )
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
        _log.info("Using temporary build directory", self.temp_directory)
        self.temp_directory.mkdir(parents=True, exist_ok=True)

        # Copy dockerfile
        self.copy_dockerfile()
        # Copy all temporary files
        for k, v in self.context_directories.items():
            self.retrieve_directory(**v)

        _log.info('start building', self.dockerfile)
        response = self.client.build(
            path=str(self.temp_directory), decode=True, tag=tag
        )
        last_event = None
        for line_parsed in response:
            self._print_docker_output(line_parsed)
            last_event = line_parsed

        if last_event is not None and 'stream' in last_event:
            match = re.search(r'Successfully built ([0-9a-f]+)',
                              last_event.get('stream', ''))
            if match:
                image_id = match.group(1)
                self.img = image_id

    def _print_docker_output(self, line_parsed):
        """
        Parse docker output
        """
        if 'stream' in line_parsed:
            print(line_parsed['stream'], end='', flush=True)
        elif 'error' in line_parsed:
            print(line_parsed['error'])
        else:
            print(line_parsed)

    def push(self, repository, tag=None):
        """
        docker push
        """
        if self.img is None:
            raise RuntimeError("[Error] Image not built, cannot push")

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
            raise RuntimeError("[Error] Image not built, cannot tag")

        success = self.client.tag(self.img, repository, tag, force)
        tag_name = self.tag_name(repository, tag)

        if success:
            _log.infofmt('Successfully tagged {} with {}', self.img, tag_name)
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

    def build_and_push(self, repo, tag=None):
        """
        Equivalent to build(), tag(), and then push()
        """
        self.build()
        self.tag(repo, tag=tag)
        self.push(repo, tag=tag)

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
                _log.info("Removing cached files at", target_path)
                shutil.rmtree(str(target_path))
            else:
                _log.info("Using cached files at", target_path)
                return
        source = path
        target = str(target_path)
        _log.infofmt('cp -r {} {}', source, target)
        shutil.copytree(source, target)
        return

    def copy_dockerfile(self):
        """
        copy dockerfile to temp directory
        """
        dockerfile_path = (self.temp_directory / 'Dockerfile')
        _log.infofmt('Copying dockerfile from {} to {}',
                     self.dockerfile, dockerfile_path)
        with dockerfile_path.open('w') as f:
            with self.dockerfile.open('r') as f_in:
                for line in f_in:
                    f.write(line)
