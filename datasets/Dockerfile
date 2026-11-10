# Use the CUDA/cuDNN Ubuntu base image
FROM --platform=linux/amd64 ubuntu:22.04

# Prevent interactive prompts during apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Update PATH and set Neve environment variables
ENV NEVE_LIBS=/root/.local/neve/lib
ENV NSK_LIBS=/root/.local/neve/lib
ENV PATH="/root/.local/bin:/root/.local/neve/bin:/usr/local/go/bin:${PATH}"

# Install essential OS packages, Python 3, and merged dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    make \
    vim \
    python3 \
    python3-pip \
    python3-dev \
    lsb-release \
    wget \
    curl \
    bzip2 \
    ca-certificates \
    gnupg \
    software-properties-common \
    libsqlite3-dev \
    sqlite3 \
    libatomic1 \
    libffi8 \
    libedit2 \
    zlib1g \
    zlib1g-dev \
    libzstd1 \
    libzstd-dev \
    libxml2 \
    libtinfo6 \
    && rm -rf /var/lib/apt/lists/*

# Install LLVM 21 toolchain
RUN curl -fsSL https://apt.llvm.org/llvm-snapshot.gpg.key | gpg --dearmor -o /usr/share/keyrings/llvm.gpg \
    && printf '%s\n' 'deb [signed-by=/usr/share/keyrings/llvm.gpg] https://apt.llvm.org/jammy/ llvm-toolchain-jammy-21 main' > /etc/apt/sources.list.d/llvm21.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends clang-21 llvm-21-dev \
    && rm -rf /var/lib/apt/lists/*


RUN wget -qO- https://github.com/NoSavedDATA/Neve/releases/download/neve-bin/install.sh | bash


# Install libraries
RUN nsm i danielcasanova12/db && nsm i danielcasanova12/batchbench

# Set up the working directory
WORKDIR /frost_exp/Neve_benchmarks/datasets

COPY . .

# Set bash as the default command
CMD ["bash"]
