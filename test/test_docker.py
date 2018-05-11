from symphony.addons import DockerBuilder

# do not prefix function name with test as we don't want pytest to do all these stuff
def build():
    dockerfile = '~/surreal/symphony/test/test_docker_Dockerfile'
    context_directories = [
        {
            'name': 'surreal',
            'path': '~/surreal/Surreal',
            'force_update': False,
        },
        {
            'name': 'tensorplex',
            'path': '~/surreal/Tensorplex',
            'force_update': True,
        }
    ]
    temp_directory = '~/symph_tmp/'
    repo = 'us.gcr.io/surreal-dev-188523/symphony-test'
    tag = 'latest'

    builder = DockerBuilder(dockerfile, context_directories, temp_directory, verbose=True)

    builder.build()

    builder.tag(repo, tag)

    builder.push(repo, tag)

if __name__ == '__main__':
    build()