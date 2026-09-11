# Use the CUDA/cuDNN Ubuntu base image
FROM nvidia/cuda:12.3.2-cudnn9-devel-ubuntu22.04

# Prevent interactive prompts during apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Update PATH so 'neve' and 'nsm' are available immediately
ENV PATH="/root/.local/bin:${PATH}"

# Install essential OS packages
RUN apt-get update && apt-get install -y \
    git \
    make \
	vim \
    lsb-release \
    wget \
    software-properties-common \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Neve packet manager
RUN wget -qO- https://github.com/NoSavedDATA/Neve/releases/download/neve-bin/install.sh | bash


# Set up the working directory
WORKDIR /frost_exp/Neve_benchmarks

# Copy the local repository files into the container
COPY . .

# Set bash as the default command
CMD ["bash"]
