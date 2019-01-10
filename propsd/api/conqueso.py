import logging

from flatdict import FlatDict

from propsd.sourcemanager import SourceManager

logger = logging.getLogger(__name__)


def _make_java_properties(data: dict) -> str:
    props = []
    for key in data:
        if isinstance(data[key], bool):
            val = str(data[key]).lower()
        else:
            val = data[key]
        props.append("{}={}".format(key, val))
    return '\n'.join(props)


def _translate_conqueso_addresses(properties: dict) -> dict:
    for service_name, service_data in properties.get('consul', {}).items():
        cluster = service_data.get('cluster')
        properties["conqueso.{}.ips".format(cluster)] = ','.join(service_data.get('addresses'))
    properties.pop('consul', None)
    return properties


async def conqueso():
    props = SourceManager.properties()

    # Remove instance data and tags
    props.pop('instance', None)
    props.pop('tags', None)

    translated = _translate_conqueso_addresses(props)
    flat = dict(FlatDict(translated, delimiter='.'))
    results = _make_java_properties(flat)
    return results


async def nested_conqueso(role, nested_property):
    props = SourceManager.properties()
