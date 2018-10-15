import os
from setuptools import setup, find_packages


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read().strip()

setup(
    name='symphony',
    version='0.9',
    author='Surreal AI team',
    url='https://github.com/SurrealAI/symphony',
    long_description=read('README.rst'),
    description='a distributed process orchestration platform that supports both laptop and major cloud providers',
    keywords=['Orchestration', 'Kubernetes', 'Tmux'],
    license='GPLv3',
    packages=[
        package for package in find_packages() if package.startswith("symphony")
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Environment :: Console",
        "Programming Language :: Python :: 3"
    ],
    install_requires=[
        "libtmux",
        "nanolog",
        "docker",
        "pyyaml",
        "libtmux",
        "benedict>=0.3",
        "nanolog",
    ],
    python_requires='>=3.5',
    include_package_data=True,
    zip_safe=False
)
