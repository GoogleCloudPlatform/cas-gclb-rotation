#!/bin/bash
# Build and run the app container locally, then watch its logs.
# Useful for debugging.
# Pre-requisites:
# 1) gcloud auth application-default login
# 2) gcloud config set core/proejct <your-project>

IMAGE_TAG='gclb-test'

docker build -t "${IMAGE_TAG}:1.0" app/.

# Kill/prune all existing containers.
docker ps | grep "$IMAGE_TAG" | sed -e 's/ .*//' | xargs docker kill
docker container prune -f

CONTAINER_ID="$(docker run \
    --publish 8000:8080 \
    --detach \
    --name gclb-test \
    -e PROJECT=$(gcloud config get-value project) \
    -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/adc.json \
    -v ~/.config/gcloud/application_default_credentials.json:/tmp/keys/adc.json:ro \
    gclb-test:1.0)"
docker ps

docker container logs -f "$CONTAINER_ID"
