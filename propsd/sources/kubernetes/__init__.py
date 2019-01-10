import logging
from typing import Optional
import socket
from kubernetes import client, config

from propsd.enums import SourceEvents
from propsd.sources.factory import SourceFactory
from propsd.sources.source import Source

_k8s_namespace_file = '/var/run/secrets/kubernetes.io/serviceaccount/namespace'


@SourceFactory('kubernetes')
class KubernetesSource(Source):
    _logger: logging.Logger = logging.getLogger(__name__)
    _enabled: bool = True

    def __init__(self, opts: Optional[dict] = None):
        super().__init__('kubernetes', 1, opts)
        try:
            config.load_incluster_config()
        except config.config_exception.ConfigException:
            self._enabled = False
            self.shutdown()
            self._send_event(SourceEvents.UPDATE, source=self, data={})
            return
        # K8s sets the pod's hostname to the canonical pod name. We can use this with the proper RBAC permissions
        # to begin exploring information about the pod, its service, and pretty much anything else we want.
        self._pod_name = socket.getfqdn()
        # Now we get the namespace the pod is deployed in.
        self._namespace = ''
        with open(_k8s_namespace_file, 'r') as f:
            self._namespace = f.read()
        self._client = client.CoreV1Api()

    def _get(self):
        if not self._enabled:
            self._logger.debug('Source/K8S: Source is disabled because we are not running in a k8s cluster.')
        pass

