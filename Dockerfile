# 'dev' or 'release' container build
ARG BUILD_TYPE=dev

# Use an official Python base image from the Docker Hub
FROM python:3.10-slim AS miniboss-base

# Install browsers
RUN apt-get update && apt-get install -y \
    chromium-driver firefox-esr \
    ca-certificates

# Install utilities
RUN apt-get install -y curl jq wget git

# Set environment variables
ENV PIP_NO_CACHE_DIR=yes \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install the required python packages globally
ENV PATH="$PATH:/root/.local/bin"
COPY requirements.txt .
COPY auto-gpt/requirements.txt ./requirements2.txt

# Set the entrypoint
ENTRYPOINT ["python", "-m", "miniboss"]

# dev build -> include everything
FROM miniboss-base as miniboss-dev
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements2.txt
WORKDIR /app
ONBUILD COPY . ./

# release build -> include bare minimum
FROM miniboss-base as miniboss-release
RUN sed -i '/Items below this point will not be included in the Docker Image/,$d' requirements.txt && \
	pip install --no-cache-dir -r requirements.txt &&\
	pip install --no-cache-dir -r requirements2.txt
WORKDIR /app
ONBUILD COPY autogpt/ ./autogpt
ONBUILD COPY miniboss/ ./miniboss

FROM miniboss-${BUILD_TYPE} AS mini-boss
