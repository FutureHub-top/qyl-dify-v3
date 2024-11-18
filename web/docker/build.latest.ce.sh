#!/bin/bash
#
# Build the latest version of the API image
#

# Unset the KUBECONFIG
unset KUBECONFIG

# Build the image
echo "1=> Building Docker Image:"
cd .. && docker buildx build -f ./Dockerfil-CE -t racio-web-amd64:latest --build-arg EDITION=SELF_HOSTED --platform=linux/amd64/v3 -o type=docker .

# Tag the image
echo "2=> Tag Docker Image (CE):"
docker tag racio-web-amd64:latest tencent/racio-web:3.9.1-$(date +%y%m%d)-CE

# List the image
echo "3=> Listing all Docker images:"
docker images | grep racio-web