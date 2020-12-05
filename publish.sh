#!/bin/bash

REGION='us-west1'
SERVICE_NAME='gclb-test'
PROJECT_ID="$(gcloud config get-value project)"
IMAGE_TAG="gcr.io/$PROJECT_ID/gclb-test"

gcloud builds submit app/ --tag "$IMAGE_TAG"
gcloud run deploy "$SERVICE_NAME" --image "$IMAGE_TAG" --region "$REGION"
