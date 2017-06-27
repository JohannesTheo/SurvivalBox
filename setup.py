import os

from setuptools import find_packages
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

install_requires = [
    "ple"
]

setup(
	name='survival-box',
	version='0.0.1',
	description='Survival Box',
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.5",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
	url='',
	author='Johannes Theodoridis',
	author_email='first lower case letter of first name plus first lower case letter of last name plus 031 at hdm-stuttgart.de',
	keywords='',
	license="MIT",
	packages=find_packages(),
        include_package_data=False,
        zip_safe=False,
        install_requires=install_requires
)
