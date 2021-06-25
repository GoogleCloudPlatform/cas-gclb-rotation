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
Entry point to the certificate rotation workflow.
"""
import logging
import os

from flask import Flask
from googleapiclient import discovery

from cert_rotator import RotationWorkflow
from config import AppConfig, AppContext, RotationProfile, loadConfig


def buildContext() -> AppContext:
    """Builds the config and GCP clients. Intended to be called at initialization time."""
    return AppContext(config=loadConfig(),
                      computeClient=discovery.build('compute', 'v1'),
                      casClient=discovery.build('privateca', 'v1'))


def runAllProfiles(context: AppContext) -> None:
    """Starts the rotation workflows for all configured profiles."""
    # TODO: consider running each profile in a separate thread to avoid
    # having a single failure break all other profiles.
    for profile in context.config.profiles:
        instance = RotationWorkflow(context, profile)
        instance.run()

_CONTEXT: AppContext = buildContext()

if __name__ == '__main__':
    # Ignore a known warning with this library that's outside our control.
    logging.getLogger('googleapiclient.discovery_cache').setLevel(
        logging.ERROR)
    logging.getLogger().setLevel(logging.INFO)
    runAllProfiles(_CONTEXT)