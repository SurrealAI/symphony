from symphony.addons import DockerBuilder

settings = {
    'temp_directory': '~/symp_temp/demo',
    'context_directories': [
        {
            'name': 'symphony',
            'path': '~/surreal/symphony', 
            # Note, you need to put in your symphony directory to allow the builder to copy symphony from the correct directory
            'force_update': True,
        },
    ],
    'verbose': True,
    'dockerfile': 'Dockerfile',
}
builder = DockerBuilder.from_dict(settings)
builder.build()
builder.tag('us.gcr.io/surreal-dev-188523/symphony-demo', 'latest')
builder.push('us.gcr.io/surreal-dev-188523/symphony-demo', tag='latest')