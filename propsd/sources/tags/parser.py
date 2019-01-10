from propsd.sources.parser import Parser


class TagsParser(Parser):
    def parse(self, tags: dict) -> dict:
        data = {}
        for tag in tags.get('Tags', []):
            data[tag.get('Key')] = tag.get('Value')
        return data
