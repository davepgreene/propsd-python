from setuptools import setup, find_packages

setup(
    name='propsd',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'boto3==1.9.47',
        'Click==7.0',
        'consulate==0.6.0',
        'dynaconf==1.1.0',
        'Flask==1.0.2',
        'requests==2.20.1',
        'meinheld==0.6.1',
        # Config loaders
        'toml==0.10.0',
        'PyYAML==3.13',
        'configobj==5.0.6'
    ],
    entry_points='''
        [console_scripts]
        propsd=propsd:propsd
    ''',
)