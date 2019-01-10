import json
import re
from os import path as p

from propsd.sources.parser import Parser


def at_basename(path: str, metadata: dict, properties: dict):
    properties[p.basename(path)] = metadata.get(path)


def document(path: str, metadata: dict, properties: dict):
    identity_document = metadata.get(path)
    # Return early if there's no data here
    if not identity_document:
        return

    if not properties.get('identity'):
        properties['identity'] = {}

    properties['identity']['document'] = identity_document
    identity = json.loads(identity_document)

    properties['account'] = identity.get('accountId')
    properties['region'] = identity.get('region')


def pkcs7(path: str, metadata: dict, properties: dict):
    pkcs7_document = metadata.get(path)
    # Return early if there's no data here
    if not pkcs7_document:
        return

    if not properties.get('identity'):
        properties['identity'] = {}
    properties['identity']['pkcs7'] = pkcs7_document


def security_credentials(path: str, metadata: dict, properties: dict):
    match = re.compile('^{}'.format(path))
    roles = [(k, v) for k, v in metadata.items() if match.match(k)]

    # Instance does not have a Profile/Role
    if not roles:
        return

    # Instances can only have 1 IAM role
    role, credential_document = roles[0]
    role = role.replace(path, '')
    properties['iam-role'] = role
    credentials = json.loads(credential_document)

    if not properties.get('credentials'):
        properties['credentials'] = {}

    properties['credentials']['lastUpdated'] = credentials.get('LastUpdated')
    properties['credentials']['type'] = credentials.get('Type')
    properties['credentials']['accessKeyId'] = credentials.get('AccessKeyId')
    properties['credentials']['secretAccessKey'] = credentials.get('SecretAccessKey')
    properties['credentials']['expires'] = credentials.get('Expiration')


def macs(path: str, metadata: dict, properties: dict):
    mac = metadata.get('meta-data/mac')
    # Return early if there's no data here
    if not mac:
        return

    if not properties.get('interface'):
        properties['interface'] = {}
    mac_attrs = [
        'vpc-ipv4-cidr-block',
        'subnet-ipv4-cidr-block',
        'public-ipv4s',
        'mac',
        'local-ipv4s',
        'interface-id'
    ]
    for attr in mac_attrs:
        properties['interface'][attr] = metadata[p.join(path, mac, attr)]
    properties['vpc-id'] = metadata.get(p.join(path, mac, 'vpc-id'))


mappings = {
    'meta-data/ami-id': at_basename,
    'meta-data/placement/availability-zone': at_basename,
    'meta-data/hostname': at_basename,
    'meta-data/instance-id': at_basename,
    'meta-data/instance-type': at_basename,
    'meta-data/local-ipv4': at_basename,
    'meta-data/local-hostname': at_basename,
    'meta-data/public-hostname': at_basename,
    'meta-data/public-ipv4': at_basename,
    'meta-data/reservation-id': at_basename,
    'meta-data/security-groups': at_basename,
    'dynamic/instance-identity/document': document,
    'dynamic/instance-identity/pkcs7': pkcs7,
    'meta-data/iam/security-credentials/': security_credentials,
    'meta-data/mac': lambda path, metadata, properties: None,
    'meta-data/network/interfaces/macs/': macs,
    'auto-scaling-group': at_basename
}


class MetadataParser(Parser):
    def parse(self, data: dict) -> dict:
        properties = {}
        for path, fn in mappings.items():
            fn(path, data, properties)
        return properties
