from propsd.lib import Sources


async def properties():
    return Sources.properties


async def nested_properties(path):
    return path
