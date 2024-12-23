#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define variables
PROJECT_ID="streamlit-portfolio-tg"  # Replace with your GCP project ID
APP_ENGINE_REGION="us-central1"  # Replace with your App Engine region (e.g., us-central)

# Set the GCP project
echo "Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Ensure App Engine is set up for the project
echo "Checking if App Engine is set up..."
gcloud app describe || gcloud app create --region=$APP_ENGINE_REGION

# Deploy the app to App Engine
echo "Deploying the Streamlit app to App Engine..."
gcloud app deploy app.yaml --quiet

# Display the URL of the deployed app
APP_URL=$(gcloud app browse --no-launch-browser)
echo "App deployed successfully! Access it at: $APP_URL"
