from setuptools import setup, find_packages


setup(
    name='symphony',
    version='0.0.1',
    author='Surreal AI team',
    url='https://github.com/SurrealAI/symphony',
    description='a distributed process orchestration platform that supports both laptop and major cloud providers',
    keywords=['Orchestration', 'Kubernetes', 'Tmux'],
    license='GPLv3',
    packages=[
        package for package in find_packages() if package.startswith("symphony")
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        # "Topic :: Scientific/Engineering :: Artificial Intelligence",
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
