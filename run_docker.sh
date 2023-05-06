#!/usr/bin/env bash
echo "Pulling the Docker image..."
docker pull minibossgpt/mini-boss:latest

echo "Please enter your OPENAI_API_KEY: "
read OPENAI_API_KEY

echo "Running the Docker container..."
docker run -it -e OPENAI_API_KEY="$OPENAI_API_KEY" minibossgpt/mini-boss:latest
