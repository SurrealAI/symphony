import os
from setuptools import setup


# def read(fname):
#     with open(os.path.join(os.path.dirname(__file__), fname)) as f:
#         return f.read().strip()


setup(
    name='symphony',
    version='0.0.1',
    author='Surreal AI team',
    url='https://github.com/SurrealAI/symphony',
    description='a distributed process orchestration platform that supports both laptop and major cloud providers',
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
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        # "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Environment :: Console",
        "Programming Language :: Python :: 3"
    ],
    install_requires=[
        "BeneDict>=0.3"
    ],
    entry_points={
        'console_scripts': [
            'symphony=symphony.symph:main',
        ],
    },
    python_requires='>=3.5',
    include_package_data=True,
    zip_safe=False
)
