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
WORKDIR /app
RUN python -m pip install rich
RUN git clone --recursive -b stable https://github.com/Significant-Gravitas/Auto-GPT
COPY auto-gpt/requirements.txt .
COPY mini-boss-requirements.txt .
# Set the entrypoint
ENTRYPOINT ["python", "-m", "miniboss"]
#CMD ["/bin/bash"]

# dev build -> include everything
FROM miniboss-base as miniboss-dev
WORKDIR /app
COPY . .
#ONBUILD COPY auto-gpt/autogpt/ ./autogpt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r mini-boss-requirements.txt
RUN pip install -e auto-gpt



# release build -> include bare minimum
FROM miniboss-base as miniboss-release
WORKDIR /app
COPY . .
RUN sed -i '/Items below this point will not be included in the Docker Image/,$d' requirements.txt && \
	pip install --no-cache-dir -r requirements.txt &&\
	pip install --no-cache-dir -r mini-boss-requirements.txt

FROM miniboss-${BUILD_TYPE} AS mini-boss
