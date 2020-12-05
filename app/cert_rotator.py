"""
Contains the rotation workflow logic.
"""

from datetime import datetime
import logging
import pytz

from config import AppContext, RotationProfile
from crypto_utils import genRsaKeyPair
from gcp_clients import HttpsProxyClient, CertificateAuthorityServiceClient
from string_utils import genResourceId

_logger = logging.getLogger(__name__)


class RotationWorkflow:
    def __init__(self, context: AppContext, profile: RotationProfile) -> None:
        self.context = context
        self.profile = profile
        self.https_proxy_client = HttpsProxyClient(context.computeClient,
                                                   profile.lb)
        self.cas_client = CertificateAuthorityServiceClient(
            context.casClient, profile)

    def shouldRotate(self, cert: dict) -> bool:
        if cert['type'] == 'MANAGED':
            _logger.warning('Ignoring Google-managed certificate [{}].'.format(
                cert['selfLink']))
            return False

        now = datetime.utcnow().astimezone(tz=pytz.UTC)
        not_before = datetime.fromisoformat(
            cert['creationTimestamp']).astimezone(tz=pytz.UTC)
        not_after = datetime.fromisoformat(
            cert['expireTime']).astimezone(tz=pytz.UTC)

        if now > not_after:
            _logger.warning('Current certificate is expired.')
            return True

        lifetime = not_after - not_before
        remaining_time = not_after - now
        remaining_ratio = remaining_time / lifetime
        _logger.info(
            'Current certificate is still valid for {} ({:2.2%} of lifetime)'.
            format(remaining_time, remaining_ratio))
        return remaining_ratio <= self.profile.rotationThreshold

    def run(self) -> None:
        old_cert = self.https_proxy_client.getFirstCertificate()
        _logger.info('Processing cert `{}`'.format(old_cert['name']))

        if not self.shouldRotate(old_cert):
            _logger.info('Certificate does not need rotation.')
            return

        _logger.info('Certificate needs rotation.')
        cert_id = genResourceId()
        key = genRsaKeyPair()
        cert_chain = self.cas_client.issueNewCert(cert_id, key.public_key)
        new_cert_uri = self.https_proxy_client.createSslCertificate(
            'auto-{}'.format(cert_id), key.private_key, ''.join(cert_chain))
        self.https_proxy_client.setSslCertificate(new_cert_uri)
        self.https_proxy_client.deleteSslCertificate(old_cert['name'])
