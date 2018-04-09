import os
from setuptools import setup


# def read(fname):
#     with open(os.path.join(os.path.dirname(__file__), fname)) as f:
#         return f.read().strip()

# TODO: I only made changes that I know needs to happen, 
# for things I don't know I commented them out, etc. 
# @Jim you need to edit this file

setup(
    name='Symphony',
    version='0.0.1',
    author='Stanford Vision and Learning Lab',
    url='https://github.com/SurrealAI/symphony',
    description='(TODO: Jim) Stanford University Repository for Reinforcement Algorithms',
    # long_description=read('README.rst'),
    # keywords=['Reinforcement Learning',
    #           'Deep Learning',
    #           'Distributed Computing'],
    license='GPLv3',
    packages=['symphony'],
    # entry_points={
    #     'console_scripts': [
    #         'git-snapshot=surreal.kube.git_snapshot:main',
    #         'surreal-runner=surreal.main_scripts.runner:main',
    #         'kurreal=surreal.kube.kurreal:main',
    #     ]
    # },
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        # "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Environment :: Console",
        "Programming Language :: Python :: 3"
    ],
    include_package_data=True,
    zip_safe=False
)
