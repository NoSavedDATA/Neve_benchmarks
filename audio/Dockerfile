FROM ubuntu:22.04

# Prevent interactive prompts during tzdata/llvm installation
ENV DEBIAN_FRONTEND=noninteractive

# Install base prerequisites
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    make \
    lsb-release \
    wget \
    software-properties-common \
    gnupg \
    bzip2 \
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
    fish \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Download Neve install script, overwrite NEVE_LIBS path, run it, then clean up
RUN wget -qO install.sh https://github.com/NoSavedDATA/Neve/releases/download/neve-bin/install.sh \
    && sed -i 's|export NEVE_LIBS="$PREFIX/lib"|export NEVE_LIBS="/neve_libs"|g' install.sh \
    && bash install.sh \
    && rm install.sh

# Configure fish shell globally (using native fish syntax)
RUN mkdir -p /etc/fish \
    && echo 'set -gx PATH ~/.local/bin $PATH' >> /etc/fish/config.fish \
    && echo 'set -gx NEVE_LIBS /neve_libs' >> /etc/fish/config.fish

# Ensure paths are also set for bash/Docker runtime
ENV PATH="/root/.local/bin:${PATH}"
ENV NEVE_LIBS="/neve_libs"

# Make bash automatically execute fish
# Using 'exec fish' replaces the bash process with fish
RUN echo 'exec fish' >> /root/.bashrc

# Set up the working directory mapping 
WORKDIR /neve

# Default to bash (which will now immediately execute fish)
CMD ["bash"]
