# from flask import Blueprint
from quart import Blueprint
from propsd.api.properties import properties, nested_properties
from propsd.api.conqueso import conqueso

v1 = Blueprint('v1', __name__)
v1.route('/properties', strict_slashes=False)(properties)
v1.route('/properties/<path:path>')(nested_properties)
v1.route('/conqueso')(conqueso)


@v1.route('/health')
async def health():
    pass


@v1.route('/status')
async def status():
    pass
