from setuptools import setup, find_packages

setup(
    name='propsd',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'boto3==1.9.47',
        'botocore==1.12.47',
        'certifi==2018.10.15',
        'chardet==3.0.4',
        'Click==7.0',
        'consulate==0.6.0',
        'docutils==0.14',
        'dynaconf==1.1.0',
        'Flask==1.0.2',
        'idna==2.7',
        'itsdangerous==1.1.0',
        'Jinja2==2.10',
        'jmespath==0.9.3',
        'MarkupSafe==1.1.0',
        'pipdeptree==0.13.1',
        'python-box==3.2.3',
        'python-dateutil==2.7.5',
        'python-dotenv==0.9.1',
        'requests==2.20.1',
        's3transfer==0.1.13',
        'six==1.11.0',
        'toml==0.10.0',
        'urllib3==1.24.1',
        'Werkzeug==0.14.1',
        'meinheld==0.6.1'
    ],
    entry_points='''
        [console_scripts]
        propsd=propsd:propsd
    ''',
)