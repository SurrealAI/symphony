import os.path as op
from symphony.addons import DockerBuilder

# docker push destination URL
UPSTREAM_URL = 'us.gcr.io/jimfan2018-208323/symphony-demo'


settings = {
    # CHANGE THIS PATH
    'temp_directory': '~/Temp/symphony',
    'context_directories': [
        {
            # CHANGE THIS PATH
            'path': '~/Dropbox/Portfolio/symphony',
            'name': 'symphony',
            'force_update': True,
        },
        {
            # CHANGE THIS PATH
            'path': '~/Dropbox/Portfolio/caraml',
            'name': 'caraml',
            'force_update': True,
        },
    ],
    'verbose': True,
    'dockerfile': 'Dockerfile',
}

builder = DockerBuilder.from_dict(settings)
builder.build()
builder.tag(UPSTREAM_URL, 'latest')
builder.push(UPSTREAM_URL, 'latest')
