FROM nvidia/cuda:12.3.2-cudnn9-devel-ubuntu22.04

# Prevent interactive prompts during tzdata/llvm installation
ENV DEBIAN_FRONTEND=noninteractive

# Install base prerequisites + libpython3.10-dev for Python Interop
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
    libpython3.10-dev \
    pip \
    zip \
    unzip \
    ca-certificates \
    apt-transport-https \
    fish \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Install LLVM 21
RUN wget https://apt.llvm.org/llvm.sh \
    && chmod +x llvm.sh \
    && ./llvm.sh 21 all \
    && rm llvm.sh

# Install compiler tools, libraries, and utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    llvm \
    clang \
    zlib1g-dev \
    libzstd-dev \
    libeigen3-dev \
    libopencv-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Neve
RUN wget -qO- https://github.com/NoSavedDATA/Neve/releases/download/neve-bin/install.sh | bash

# Install uv (astral.sh)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Ensure uv is in PATH for the next RUN command
ENV PATH="/root/.local/bin:${PATH}"

# Install Mojo and evaluation packages in the shared virtual environment
RUN uv venv /opt/mojo-venv && \
    . /opt/mojo-venv/bin/activate && \
    uv pip install mojo --index https://whl.modular.com/nightly/simple/ --prerelease allow && \
    uv pip install scikit-learn pandas numpy

# Configure environment variables for runtime
ENV PATH="/opt/mojo-venv/bin:/root/.local/bin:${PATH}"
ENV NEVE_LIBS="/root/.local/neve/lib"
ENV MODULAR_HOME="/opt/mojo-venv"
ENV MOJO_PYTHON_LIBRARY="/usr/lib/x86_64-linux-gnu/libpython3.10.so"

# Locate the Mojo standard library directory dynamically and configure fish/bash
RUN MOJO_LIB_DIR=$(find /opt/mojo-venv -type d -path "*/site-packages/mojo/lib" | head -n 1) \
    && mkdir -p /etc/fish \
    && echo 'set -gx PATH /opt/mojo-venv/bin ~/.local/bin $PATH' >> /etc/fish/config.fish \
    && echo 'set -gx NEVE_LIBS ~/.local/neve/lib' >> /etc/fish/config.fish \
    && echo 'set -gx MODULAR_HOME /opt/mojo-venv' >> /etc/fish/config.fish \
    && echo 'set -gx MOJO_PYTHON_LIBRARY /usr/lib/x86_64-linux-gnu/libpython3.10.so' >> /etc/fish/config.fish \
    && echo "set -gx MOJO_INCLUDE_PATH $MOJO_LIB_DIR" >> /etc/fish/config.fish \
    && echo "export MOJO_INCLUDE_PATH=$MOJO_LIB_DIR" >> /root/.bashrc

# Make bash automatically execute fish
RUN echo 'exec fish' >> /root/.bashrc

# Download and extract the datasets
RUN mkdir -p /root/Datasets/iris && \
    cd /root/Datasets/iris && \
    wget https://archive.ics.uci.edu/static/public/53/iris.zip && \
    unzip iris.zip && \
    rm iris.zip

RUN mkdir -p /root/Datasets && \
    cd /root/Datasets && \
    wget https://archive.ics.uci.edu/static/public/240/human+activity+recognition+using+smartphones.zip && \
    unzip human+activity+recognition+using+smartphones.zip && \
    rm -rf human+activity+recognition+using+smartphones.zip && \
    unzip "UCI HAR Dataset.zip" && \
    rm -rf "UCI HAR Dataset.names" && \
    rm -rf "UCI HAR Dataset.zip" && \
    rm -rf __MACOSX && \
    mv "UCI HAR Dataset" har

# Install the requested Neve packages
RUN nsm i NoSavedDATA/frost && \
    nsm i NoSavedDATA/csv
