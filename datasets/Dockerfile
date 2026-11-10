FROM --platform=linux/amd64 ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends git curl wget bzip2 ca-certificates gnupg make python3 libsqlite3-dev sqlite3 libatomic1 libffi8 libedit2 zlib1g libzstd1 libxml2 libtinfo6 && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://apt.llvm.org/llvm-snapshot.gpg.key | gpg --dearmor -o /usr/share/keyrings/llvm.gpg && printf '%s\n' 'deb [signed-by=/usr/share/keyrings/llvm.gpg] https://apt.llvm.org/jammy/ llvm-toolchain-jammy-21 main' > /etc/apt/sources.list.d/llvm21.list && apt-get update && apt-get install -y --no-install-recommends clang-21 llvm-21-dev && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /tmp/neve-install && cd /tmp/neve-install && curl -fsSL https://github.com/NoSavedDATA/Neve/releases/download/neve-bin/install.sh -o install.sh && bash install.sh
ENV NEVE_LIBS=/root/.local/neve/lib
ENV NSK_LIBS=/root/.local/neve/lib
ENV PATH=/root/.local/bin:/root/.local/neve/bin:$PATH
ARG SQLITE_REPOSITORY=danielcasanova12/db
RUN nsm i "$SQLITE_REPOSITORY" && test -s "$NEVE_LIBS/db/lib.so"
WORKDIR /project
COPY . .
RUN bash setup.sh
CMD ["bash"]
