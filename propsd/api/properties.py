from propsd.api import blueprint


@blueprint.route('/properties', strict_slashes=False)
def properties():
    return 'foo'
