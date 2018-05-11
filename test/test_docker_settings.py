from symphony.addons import DockerRecordMaster

data = [
    {
        'name': 'test',
        'temp_directory': '/tmp/symphonyabc',
        'context_directories': [
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
        ],
        'verbose': False,
        'dockerfile': 'test_docker_Dockerfile1',
    },
    {
        'name': 'test2',
        'dockerfile': 'test_docker_Dockerfile2',
    },
    {
        'name': 'test_incorrect',
        'verbose': True,
        # 'dockerfile': 'test_docker_Dockerfile',
    }
]

correct = {
            'tensorplex': {
                'force_update': True, 
                'name': 'tensorplex', 
                'path': '/Users/jirenz/surreal/Tensorplex'
            },
            'surreal': {
                'force_update': False, 
                'name': 'surreal', 
                'path': '/Users/jirenz/surreal/Surreal'
            },
        }

def test_load_full():
    master = DockerRecordMaster()
    master.add_config(data[0])
    builder = master.get('test')
    assert str(builder.temp_directory) == '/tmp/symphonyabc/symphony_docker_build'
    assert builder.context_directories == correct
    assert not builder.verbose
    assert str(builder.dockerfile) == 'test_docker_Dockerfile1'

def test_load_default():
    master = DockerRecordMaster()
    master.add_config(data[1])
    builder = master.get('test2')
    assert str(builder.temp_directory) == '/tmp/symphony/symphony_docker_build'
    assert builder.verbose
    assert builder.context_directories == {}
    assert str(builder.dockerfile) == 'test_docker_Dockerfile2'

def test_load_all():
    master = DockerRecordMaster()
    master.load_all(data[:2])

def test_load_incorret():
    master = DockerRecordMaster()
    try:
        master.load_all(data)
    except ValueError:
        pass

def test_load_keyerror():
    master = DockerRecordMaster()
    try:
        master.get('nonexistant')
    except KeyError:
        pass
