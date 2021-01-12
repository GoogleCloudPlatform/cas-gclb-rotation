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
Contains helper functions for dealing with formatting and resource names.
"""

import base64
import datetime
import random
import re
import string
from typing import Optional

_MICROSECOND_PRECISION = 6
_RNG = random.SystemRandom()
_ALPHANUMERICS = string.ascii_lowercase + string.digits


def genResourceId() -> str:
    """Generates a new random resource ID beginning with today's date (for easy identification)."""
    return '{}-{}-{}'.format(
        datetime.datetime.now().strftime('%Y%m%d'),
        ''.join(_RNG.choice(_ALPHANUMERICS) for i in range(3)),
        ''.join(_RNG.choice(_ALPHANUMERICS) for i in range(3)))


def parseResourceId(resource_uri: str, resource_type: str) -> Optional[str]:
    """Parses the resource ID of the given type from the given URI, or returns None if not found."""
    matches = re.search('{}/([^/]+)'.format(resource_type), resource_uri)
    if not matches:
        return None

    return matches.group(1)


def serializeDurationForJson(duration: datetime.timedelta) -> str:
    """Serializes the given duration for inclusion in a JSON request body."""
    num = '{}'.format(round(duration.total_seconds(), _MICROSECOND_PRECISION))
    if num.endswith('.0'):
        num = num[:-len('.0')]
    return num + 's'


def serializePemBytesForJson(pem: bytes) -> str:
    """Serializes the given PEM-encoded bytes for inclusion in a JSON request body."""
    return base64.b64encode(pem).decode('utf-8')
