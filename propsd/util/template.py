from jinja2 import Undefined


class PreserveUndefined(Undefined):
    def __getitem__(self, *args, **kwargs):
        field = args[0] if args[0] else None
        return '{{{{ {}:{} }}}}'.format(self._undefined_name, field)
