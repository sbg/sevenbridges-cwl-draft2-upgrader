from datetime import datetime
from setuptools import setup, find_packages
import os


NAME = 'sbg_cwl_upgrader'
VERSION = '0.2.0'
DIR = os.path.abspath(os.path.dirname(__file__))
NOW = datetime.utcnow()

with open(os.path.join(DIR, 'README.md')) as f:
    long_description = f.read()

with open(os.path.join(DIR, 'requirements.txt')) as f:
    install_requires = f.read()

packages = find_packages()

setup(
    name='sevenbridges-cwl-draft2-upgrader',
    version=VERSION,
    packages=find_packages(),
    url='https://github.com/sbg/sevenbridges-cwl-draft2-upgrader',
    platforms=['POSIX', 'MacOS'],
    python_requires='>=3.6.0',
    install_requires=install_requires,
    maintainer='Seven Bridges Genomics Inc.',
    maintainer_email='bogdan.gavrilovic@sbgenomics.com',
    description='Seven Bridges CWL sbg:draft2 to v1.0 upgrader.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    include_package_data=True,
    keywords=['sevenbridges', 'sbg', 'cwl'],
    use_2to3=True,
    test_suite='tests',
    license='Apache Software License 2.0',
    entry_points={
        'console_scripts': [
            'sbg_cwl_upgrader = ' +
            NAME + '.converter.sbg_draft2_to_cwl_1_0:main',
            'sbg_validate_js_cwl_v1 = ' +
            NAME + '.validator.sbg_validate_js_cwl_v1:main',
            'sbg_cwl_decomposer = ' +
            NAME + '.decomposer.sbg_cwl_decomposer:main'
            ]
    },
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
    ]
)
