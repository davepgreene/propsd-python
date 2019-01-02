import logging
import os
import time
from pathlib import Path

import boto3
import click
from botocore.client import Config
from localstack.services.infra import start_infra
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from propsd.util import debounce

logger = logging.getLogger(__name__)

sample_data_path = Path(__file__).parent / 'sample_data'
bucket_name = 'propsd'
s3_resource = boto3.resource('s3', 'us-east-1',
                             endpoint_url='http://localhost:4572',
                             use_ssl=False,
                             config=Config(s3={'addressing_style': 'path'}))


class S3SyncFSEventHandler(FileSystemEventHandler):
    def __init__(self, path, bucket):
        super()
        self._path = path
        self._bucket = bucket

    @debounce(0.5)
    def on_any_event(self, event):
        self.sync_s3_data()

    def sync_s3_data(self):
        logger.info('Helpers/S3: Synchronizing files.')
        # First clear the bucket
        self._bucket.delete_objects(Delete={
            'Objects': [{'Key': o.key} for o in self._bucket.objects.all()]
        })
        # Then upload all the files
        for filename, key in self._get_all_files():
            self._bucket.upload_file(filename, key)
        logger.info('Helpers/S3: Synchronization complete.')

    def _get_all_files(self):
        all_files = []
        for root, _, files in os.walk(self._path):
            all_files += [
                (
                    str(Path(root).joinpath(f)),
                    str(Path(root).joinpath(f).relative_to(self._path))
                ) for f in files
            ]
        return all_files


@click.command()
@click.option('--verbose', '-v', is_flag=True, default=False, help='Verbose logging')
def s3(verbose):
    os.environ['HOSTNAME'] = '0.0.0.0'
    os.environ['HOSTNAME_EXTERNAL'] = '0.0.0.0'
    if verbose:
        os.environ['DEBUG'] = '1'
    thread = start_infra(asynchronous=True, apis=['s3'])
    logger.info('Helpers/S3: Creating bucket: %s', bucket_name)

    bucket_resource = s3_resource.Bucket(bucket_name)
    bucket_resource.create()

    event_handler = S3SyncFSEventHandler(sample_data_path, bucket_resource)
    observer = Observer()
    observer.schedule(event_handler, str(sample_data_path), recursive=True)
    observer.start()

    event_handler.sync_s3_data()
    try:
        while True:
            time.sleep(1)
    except (RuntimeError, KeyboardInterrupt):
        observer.stop()
        logger.info('Helpers/S3: Shutting down.')
        thread.stop()
    observer.join()
