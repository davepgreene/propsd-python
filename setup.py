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
        'quart==0.6.10',
        'requests==2.20.1',
        'meinheld==0.6.1',
        'apscheduler==3.5.3',
        'aiohttp==3.4.4',
        # Config loaders
        'toml==0.10.0',
        'PyYAML==3.13',
        'configobj==5.0.6'
    ],
    extras_require={
        'dev': [
            'pylint==2.1.1',
            'flake8==3.5.0',
            'localstack==0.8.8',
            'amazon-kclpy==1.5.0',
            'watchdog==0.9.0'
        ]
    },
    entry_points="""
        [console_scripts]
        propsd=propsd:propsd
        metadata-mock=propsd.helpers.metadata:metadata
        s3-mock=propsd.helpers.s3:s3
    """,
)
