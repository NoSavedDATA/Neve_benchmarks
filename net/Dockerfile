# Use the CUDA/cuDNN Ubuntu base image
FROM ubuntu:22.04

# Prevent interactive prompts during apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Update PATH so 'neve', 'nsm', and 'go' are available immediately
ENV PATH="/root/.local/bin:/usr/local/go/bin:${PATH}"

# Install essential OS packages and Python 3
RUN apt-get update && apt-get install -y \
    git \
    make \
    vim \
    python3 \
    python3-pip \
    python3-dev \
    lsb-release \
    wget \
    curl \
    software-properties-common \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install a recent version of Go 
# (Ubuntu 22.04 apt repos have an older version, so downloading the binary is safer for benchmarks)
ENV GO_VERSION=1.22.4
RUN wget -qO- "https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz" | tar -C /usr/local -xz

# Install Neve packet manager
RUN wget -qO- https://github.com/NoSavedDATA/Neve/releases/download/neve-bin/install.sh | bash

RUN nsm i NoSavedDATA/net

# Set up the working directory
WORKDIR /frost_exp/Neve_benchmarks/net

# OPTIONAL: Copy dependency manifests first to leverage Docker layer caching.
# If you do this, Docker won't re-download PyTorch/Go packages every time you change your code.
# COPY requirements.txt go.mod go.sum ./
# RUN pip3 install --no-cache-dir -r requirements.txt
# RUN go mod download

# Copy the local repository files into the container
COPY . .

# If you don't use requirements.txt/go.mod, you can install dependencies directly here:
# RUN pip3 install --no-cache-dir torch numpy
# RUN go mod tidy

# Set bash as the default command
CMD ["bash"]
