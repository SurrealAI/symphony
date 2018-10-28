# from symphony.addons import DockerBuilder

# data = {
#     'test': {
#         'temp_directory': '/tmp/symphonyabc',
#         'context_directories': [
#             {
#                 'name': 'surreal',
#                 'path': '~/surreal/Surreal',
#                 'force_update': False,
#             },
#             {
#                 'name': 'tensorplex',
#                 'path': '~/surreal/Tensorplex',
#                 'force_update': True,
#             }
#         ],
#         'verbose': False,
#         'dockerfile': 'test_docker_Dockerfile1',
#     },
#     'test2': {
#         'dockerfile': 'test_docker_Dockerfile2',
#     },
#     'test3': {
#         'name': 'test_incorrect',
#         'verbose': True,
#         # 'dockerfile': 'test_docker_Dockerfile',
#     }
# }

# correct = {
#             'tensorplex': {
#                 'force_update': True, 
#                 'name': 'tensorplex', 
#                 'path': '~/surreal/Tensorplex'
#             },
#             'surreal': {
#                 'force_update': False, 
#                 'name': 'surreal', 
#                 'path': '/Users/jirenz/surreal/Surreal'
#             },
#         }

# def test_load_full():
#     builder = DockerBuilder.from_dict(data['test'])
#     assert str(builder.temp_directory) == '/tmp/symphonyabc/symphony_docker_build'
#     assert builder.context_directories == correct
#     assert str(builder.dockerfile) == 'test_docker_Dockerfile1'

# def test_load_default():
#     builder = DockerBuilder.from_dict(data['test2'])
#     assert str(builder.temp_directory) == '/tmp/symphony/symphony_docker_build'
#     assert builder.context_directories == {}
#     assert str(builder.dockerfile) == 'test_docker_Dockerfile2'

# def test_load_incorret():
#     try:
#         builder = DockerBuilder.from_dict(data['test3'])
#     except ValueError:
#         pass
