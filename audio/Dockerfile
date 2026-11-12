FROM ubuntu:22.04

# Prevent interactive prompts during apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Update PATH and set Neve environment variables
ENV NEVE_LIBS=/root/.local/neve/lib
ENV PATH="/root/.local/bin:/root/.local/neve/bin:${PATH}"

# Install essential OS packages and Python 3
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    make \
    vim \
    python3 \
    python3-pip \
    lsb-release \
    wget \
    curl \
    bzip2 \
    util-linux \
    ca-certificates \
    gnupg \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Install LLVM 21 toolchain (the audio lib's deps.sh builds lib.so with it if the release has none)
RUN curl -fsSL https://apt.llvm.org/llvm-snapshot.gpg.key | gpg --dearmor -o /usr/share/keyrings/llvm.gpg \
    && printf '%s\n' 'deb [signed-by=/usr/share/keyrings/llvm.gpg] https://apt.llvm.org/jammy/ llvm-toolchain-jammy-21 main' > /etc/apt/sources.list.d/llvm21.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends clang-21 llvm-21-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Neve
RUN wget -qO- https://github.com/NoSavedDATA/Neve/releases/download/neve-bin/install.sh | bash

# Install the audio library (lib.so from its `latest` release)
RUN nsm i freds0/audio

# Python side: torch/torchaudio CPU (own index, avoids CUDA wheels) + librosa
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir torch==2.5.1 torchaudio==2.5.1 \
      --index-url https://download.pytorch.org/whl/cpu \
    && pip3 install --no-cache-dir -r /tmp/requirements.txt

# Set up the working directory
WORKDIR /frost_exp/Neve_benchmarks/audio

COPY . .

# Set bash as the default command
CMD ["bash"]
