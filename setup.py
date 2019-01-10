from setuptools import setup, find_packages

setup(
    name='propsd',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'apscheduler==3.5.3',
        'boto3==1.9.71',
        'boltons==18.0.1',
        'Click==7.0',
        'python-consul==1.1.0',
        'dynaconf==1.2.0',
        'flatdict==3.1.0',
        'Jinja2==2.10',
        'pytz==2018.7',
        'quart==0.7.1',
        'requests==2.20.1',
        'kubernetes==8.0.1',
    ] + [
        # Config loaders
        'configobj==5.0.6',
        'PyYAML==3.13',
        'toml==0.10.0',
    ],
    extras_require={
        'dev': [
            'pylint==2.2.2',
            'flake8==3.6.0',
            'localstack==0.8.9',
            'amazon-kclpy==1.5.0',
            'watchdog==0.9.0',
            'mypy==0.650'
        ]
    },
    entry_points="""
        [console_scripts]
        propsd=propsd:propsd
        metadata-mock=propsd.helpers.metadata:metadata
        s3-mock=propsd.helpers.s3:s3
    """,
)
