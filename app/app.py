"""
Entry point to the certificate rotation workflow.
"""
import logging
import os

from flask import Flask
from googleapiclient import discovery

from cert_rotator import RotationWorkflow
from config import AppConfig, AppContext, RotationProfile, loadConfig

app = Flask(__name__)


def buildContext() -> AppContext:
    """Builds the config and GCP clients. Intended to be called at initialization time."""
    return AppContext(config=loadConfig(),
                      computeClient=discovery.build('compute', 'v1'),
                      casClient=discovery.build('privateca', 'v1beta1'))


def runAllProfiles(context: AppContext) -> None:
    """Starts the rotation workflows for all configured profiles."""
    # TODO: consider running each profile in a separate thread to avoid
    # having a single failure break all other profiles.
    for profile in context.config.profiles:
        instance = RotationWorkflow(context, profile)
        instance.run()


_CONTEXT: AppContext = buildContext()


@app.route('/')
def onRequest():
    """Handles any request by beginning the rotation workflow."""
    # TODO: add some limits to ensure only 1 request is processing at a time.
    runAllProfiles(_CONTEXT)

    # Flask needs a response.
    return ''


if __name__ == '__main__':
    # Ignore a known warning with this library that's outside our control.
    logging.getLogger('googleapiclient.discovery_cache').setLevel(
        logging.ERROR)
    logging.getLogger().setLevel(logging.INFO)
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')
