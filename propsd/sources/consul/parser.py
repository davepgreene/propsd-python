import logging

from propsd.sources.parser import Parser

logger = logging.getLogger(__name__)


class ConsulParser(Parser):
    def parse(self, data: dict):
        properties = {}

        for service_name, nodes in data.items():
            addresses = []
            for node in nodes if isinstance(nodes, list) else []:
                service_address = node.get('Service', {}).get('Address')
                agent_address = node.get('Node', {}).get('Address')
                if service_address:
                    addresses.append(service_address)
                elif agent_address:
                    addresses.append(agent_address)
            properties[service_name] = {
                'cluster': service_name,
                'addresses': addresses
            }
        # We need to nest all of our consul properties in the 'consul' namespace
        return {
            'consul': properties
        }
