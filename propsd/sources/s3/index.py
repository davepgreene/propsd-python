import json
import logging
import re
from typing import Optional, List

from jinja2 import Environment

from propsd.sourcemanager import SourceManager
from propsd.sources.factory import SourceFactory
from propsd.sources.s3 import S3Source
from propsd.util import convert_to_object_access
from propsd.util.template import PreserveUndefined


@SourceFactory('s3-index')
class S3Index(S3Source):
    _sources: List[dict] = []
    _env: Environment = Environment(undefined=PreserveUndefined)
    _logger: logging.Logger = logging.getLogger(__name__)

    def __init__(self, opts: Optional[dict] = None):
        super().__init__('s3-index', 1, opts)

    def _add_sources(self, sources, to_add):
        scheduled_sources = 0
        for source_name, _ in to_add:
            source_definition = next(s for s in sources if s.get('name') == source_name)
            source_type = source_definition.get('type')
            # ...create source objects...
            Source = SourceFactory.new(source_type)  # pylint: disable=invalid-name
            if Source is None:
                # Factory didn't return anything so we can't do anything with that source
                continue
            opts = source_definition.get('parameters', {})
            try:
                instance = Source(source_definition.get('name'), opts=opts)
            except Exception as ex:  # pylint: disable=broad-except
                self._logger.error('Source/S3Index: Got the following error while creating a source of type %s: %s',
                                   source_type, ex)
                continue
            # ...and schedule them.
            SourceManager.schedule(instance)
            scheduled_sources += 1
        if scheduled_sources > 0:
            self._logger.info('Sources/S3Index: Added %d sources from the index', scheduled_sources)

    def _remove_sources(self, to_remove):
        if to_remove:
            for source in to_remove:
                SourceManager.unschedule(source)
            self._logger.info('Sources/S3Index: Removed %d sources from the index', len(to_remove))

    def _create_index_from_template(self):
        all_properties = SourceManager.properties()
        # Now we iterate through sources, resolve paths from existing parameters, and then
        # add the new sources to the SourceManager.
        #
        # First we have to prep our source object to make sure we replace `:` with a python object so
        # Jinja can index correctly.
        template = self._env.from_string(
            re.sub(r'{{ ?(.+?) ?}}', convert_to_object_access, json.dumps(self._sources))
        )
        # Then we load the fixed JSON back in so we have the built sources list.
        sources = json.loads(template.render(all_properties))
        # Add the bucket to every source dict
        for source in sources:
            type = source.get('type')
            params = source.get('parameters', {})
            if 'bucket' not in params and type == 's3':
                params['bucket'] = self._bucket
        return sources

    def _get(self):
        # We want to short circuit the source re-registration if obj ETag matches.
        obj = super()._get()
        if obj is None:
            return

        sources = self._create_index_from_template()
        # We need to calculate the diff between existing sources and new sources so we can unschedule dead jobs,
        # schedule new ones, and leave existing ones that haven't changed alone
        identity = [
            (
                s.get('name'),
                SourceManager.identity(s.get('name', '').encode('utf-8'),
                                       s.get('type', '').encode('utf-8'),
                                       s.get('parameters', {}))
            ) for s in sources
        ]
        actions = SourceManager.source_diff(identity)

        # Now we iterate through the resolved sources we need to add...
        self._add_sources(sources, actions.get('add', []))
        self._remove_sources(actions.get('remove', []))
