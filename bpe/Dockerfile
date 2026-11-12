FROM ubuntu:22.04

# Prevent interactive prompts during tzdata/llvm installation
ENV DEBIAN_FRONTEND=noninteractive

# Install base prerequisites + libpython3.10-dev for Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    make \
    lsb-release \
    wget \
    curl \
    software-properties-common \
    gnupg \
    python3-dev \
    python3-venv \
	bzip2 \
    libpython3.10-dev \
    pip \
    zip \
    unzip \
	libatomic1 \
    ca-certificates \
    apt-transport-https \
    fish \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Install Neve
RUN wget -qO- https://github.com/NoSavedDATA/Neve/releases/download/neve-bin/install.sh | bash

# Install uv (astral.sh)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Ensure uv is in PATH for the next RUN command
ENV PATH="/root/.local/bin:${PATH}"

# Install standard Python virtual environment and required libraries
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip install psutil sentencepiece scikit-learn pandas numpy datasets

# Configure environment variables for runtime
ENV PATH="/opt/venv/bin:/root/.local/bin:${PATH}"
ENV NEVE_LIBS="/root/.local/neve/lib"

# Configure fish and bash paths
RUN mkdir -p /etc/fish \
    && echo 'set -gx PATH /opt/venv/bin ~/.local/bin $PATH' >> /etc/fish/config.fish \
    && echo 'set -gx NEVE_LIBS ~/.local/neve/lib' >> /etc/fish/config.fish

RUN echo 'exec fish' >> /root/.bashrc

COPY download_openwebtext.py /tmp/download_openwebtext.py

RUN mkdir -p /Datasets/openwebtxt && \
    /opt/venv/bin/python /tmp/download_openwebtext.py && \
    rm /tmp/download_openwebtext.py

RUN nsm i NoSavedDATA/csv

WORKDIR /frost_exp/Neve_benchmarks/bpe
