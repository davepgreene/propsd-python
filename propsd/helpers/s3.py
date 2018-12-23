import os
from pathlib import Path
import time
import logging
from localstack.services.infra import start_infra
import click
import boto3
from botocore.client import Config
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)

sample_data_path = Path(__file__).parent / 'sample_data'
bucket_name = 'propsd'
s3_resource = boto3.resource('s3', 'us-east-1',
                             endpoint_url='http://localhost:4572',
                             use_ssl=False,
                             config=Config(s3={'addressing_style': 'path'}))


def debounce(seconds):
    """Decorator ensures function that can only be called once every `s` seconds.
    """
    def decorate(fn):
        first_execution = None

        def wrapped(*args, **kwargs):
            nonlocal first_execution
            current_time = time.time()
            if first_execution is None or current_time - first_execution >= seconds:
                result = fn(*args, **kwargs)
                first_execution = time.time()
                return result
            return None
        return wrapped
    return decorate


class S3SyncFSEventHandler(FileSystemEventHandler):
    def __init__(self, path, bucket):
        super()
        self._path = path
        self._bucket = bucket

    @debounce(0.5)
    def on_any_event(self, event):
        self.sync_s3_data()

    def sync_s3_data(self):
        logger.info('Synchronizing files.')
        # First clear the bucket
        self._bucket.delete_objects(Delete={
            'Objects': [{'Key': o.key} for o in self._bucket.objects.all()]
        })
        # Then upload all the files
        for filename, key in self._get_all_files():
            self._bucket.upload_file(filename, key)
        logger.info('Synchronization complete.')

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
def s3():
    thread = start_infra(asynchronous=True, apis=['s3'])
    logger.info('Creating bucket: %s', bucket_name)

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
        logger.info('Shutting down.')
        thread.stop()
    observer.join()
