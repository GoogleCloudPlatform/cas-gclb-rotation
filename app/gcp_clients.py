# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Contains client code that interact with GCP services.
"""

import datetime
import logging
from typing import List
import uuid

from googleapiclient.http import HttpRequest
from googleapiclient import discovery

from config import AppContext, RotationProfile, SimpleResource
from crypto_utils import CryptoKeyPair
from string_utils import genResourceId, parseResourceId, serializeDurationForJson, serializePemBytesForJson


def logAndExecute(request: HttpRequest):
    """Executes the given request while adding debug logs for the request and response."""
    logging.debug('Request: {}'.format(request.to_json()))
    response = request.execute()
    logging.debug('Response: {}'.format(response))
    return response


class HttpsProxyClient:
    """Exposes operations on httpsTargetProxies and sslCertificates."""
    def __init__(self, discovery_client: discovery.Resource,
                 lb: SimpleResource):
        self.discovery_client = discovery_client
        self.project = lb.project
        self.location = lb.location
        self.is_global = lb.isGlobal()
        self.lb_id = lb.name

    def awaitOperation(self, operation: dict) -> None:
        """Waits for the given operation to complete."""
        operation_id = parseResourceId(operation['selfLink'], 'operations')
        logging.info('Awaiting operation `{}`..'.format(operation_id))
        if self.is_global:
            logAndExecute(self.discovery_client.globalOperations().wait(
                project=self.project, operation=operation_id))
        else:
            logAndExecute(self.discovery_client.regionOperations().wait(
                project=self.project,
                region=self.location,
                operation=operation_id))

        # TODO: confirm success status.

    def getFirstCertificate(self) -> dict:
        """Gets the first SslCertificate associated with the current load balancer."""
        if self.is_global:
            proxy = logAndExecute(
                self.discovery_client.targetHttpsProxies().get(
                    project=self.project, targetHttpsProxy=self.lb_id))
        else:
            proxy = logAndExecute(
                self.discovery_client.regionTargetHttpsProxies().get(
                    project=self.project,
                    region=self.location,
                    targetHttpsProxy=self.lb_id))

        # For now, only look at the first certificate.
        cert_uri = proxy['sslCertificates'][0]
        cert_id = parseResourceId(cert_uri, 'sslCertificates')

        if self.is_global:
            return logAndExecute(self.discovery_client.sslCertificates().get(
                project=self.project, sslCertificate=cert_id))
        else:
            return logAndExecute(
                self.discovery_client.regionSslCertificates().get(
                    project=self.project,
                    region=self.location,
                    sslCertificate=cert_id))

    def createSslCertificate(self, cert_id: str, private_key: bytes,
                             cert_chain: str) -> str:
        """Creates a new SslCertificate resource and returns its resource URI."""
        logging.info('Creating new SslCertificate [{}]..'.format(cert_id))
        if self.is_global:
            insertOperation = logAndExecute(
                self.discovery_client.sslCertificates().insert(
                    project=self.project,
                    body={
                        'name': cert_id,
                        'certificate': cert_chain,
                        'privateKey': private_key.decode('utf-8'),
                    },
                    requestId=str(uuid.uuid4()),
                ))
        else:
            insertOperation = logAndExecute(
                self.discovery_client.regionSslCertificates().insert(
                    project=self.project,
                    region=self.location,
                    body={
                        'name': cert_id,
                        'certificate': cert_chain,
                        'privateKey': private_key.decode('utf-8'),
                    },
                    requestId=str(uuid.uuid4()),
                ))

        self.awaitOperation(insertOperation)
        logging.info('Created [{}].'.format(insertOperation['targetLink']))
        return insertOperation['targetLink']

    def setSslCertificate(self, cert_uri: str) -> None:
        """Updates the current load balancer with the given cert."""
        logging.info('Updating load balancer [{}] with new cert..'.format(
            self.lb_id))
        if self.is_global:
            updateOperation = logAndExecute(
                self.discovery_client.targetHttpsProxies().setSslCertificates(
                    project=self.project,
                    targetHttpsProxy=self.lb_id,
                    body={
                        'sslCertificates': [cert_uri],
                    },
                    requestId=str(uuid.uuid4()),
                ))
        else:
            updateOperation = logAndExecute(
                self.discovery_client.regionTargetHttpsProxies(
                ).setSslCertificates(
                    project=self.project,
                    region=self.location,
                    targetHttpsProxy=self.lb_id,
                    body={
                        'sslCertificates': [cert_uri],
                    },
                    requestId=str(uuid.uuid4()),
                ))

        self.awaitOperation(updateOperation)
        logging.info('Updated [{}].'.format(updateOperation['targetLink']))

    def deleteSslCertificate(self, cert_id: str) -> None:
        """Deletes the given SslCertificate resource."""
        logging.info('Deleting old SslCertificate [{}]..'.format(cert_id))
        if self.is_global:
            deleteOperation = logAndExecute(
                self.discovery_client.sslCertificates().delete(
                    project=self.project, sslCertificate=cert_id))
        else:
            deleteOperation = logAndExecute(
                self.discovery_client.regionSslCertificates().delete(
                    project=self.project,
                    region=self.location,
                    sslCertificate=cert_id))

        self.awaitOperation(deleteOperation)
        logging.info('Deleted [{}].'.format(deleteOperation['targetLink']))


class CertificateAuthorityServiceClient:
    def __init__(self, discovery_client: discovery.Resource,
                 profile: RotationProfile):
        self.discovery_client = discovery_client
        self.profile = profile
        self.project = profile.issuingPool.project
        self.location = profile.issuingPool.location
        self.caPool = profile.issuingPool.name
    

    def issueNewCert(self, cert_id: str, public_key: bytes) -> List[str]:
        cert_body = {
            'lifetime': serializeDurationForJson(self.profile.lifetime),
            'config': {
                'publicKey': {
                    'key': serializePemBytesForJson(public_key),
                    'format': 'PEM',
                },
                'subjectConfig': {
                    'subject': {
                        'commonName': self.profile.dnsName,
                    },
                    'subjectAltName': {
                        'dnsNames': [self.profile.dnsName],
                    }
                },
                'x509Config': {
                    'caOptions': {
                        'isCa': False
                    },
                    'keyUsage': {
                        'baseKeyUsage': {
                            'digitalSignature': True,
                            'keyEncipherment': True,
                        },
                        'extendedKeyUsage': {
                            'serverAuth': True,
                        },
                    },
                }
            }
        }

        parent = 'projects/{}/locations/{}/caPools/{}'.format(
            self.project, self.location, self.caPool)
        request_id = str(uuid.uuid4())

        logging.info('Creating new CAS certificate..')
        certsClient = self.discovery_client.projects().locations(
        ).caPools().certificates()
        cert = logAndExecute(certsClient.create(
            parent=parent,
            body=cert_body,
            requestId=request_id,
            certificateId=cert_id,
        ))
        logging.info('Created [{}].'.format(cert['name']))

        return [cert['pemCertificate']] + cert['pemCertificateChain']
