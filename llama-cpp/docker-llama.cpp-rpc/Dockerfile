# =======================
# BUILD STAGE
# =======================
FROM ubuntu:22.04 AS build

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /build

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    ca-certificates \
    libssl-dev \
 && rm -rf /var/lib/apt/lists/*

# Clone llama.cpp
RUN git clone https://github.com/ggerganov/llama.cpp.git
WORKDIR /build/llama.cpp

# CPU-only, RPC-enabled, server-enabled build
RUN cmake -S . -B build \
    -DCMAKE_BUILD_TYPE=Release \
    -DLLAMA_SERVER=ON \
    -DLLAMA_RPC=ON \
    -DLLAMA_METAL=OFF \
    -DLLAMA_CUDA=OFF \
    -DLLAMA_VULKAN=OFF \
    -DBUILD_SHARED_LIBS=OFF \
    -DCPPHTTPLIB_OPENSSL_SUPPORT=ON

RUN cmake --build build -j$(nproc)

# =======================
# RUNTIME STAGE
# =======================
FROM ubuntu:22.04

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ca-certificates \
    libstdc++6 \
    libgomp1 \
 && rm -rf /var/lib/apt/lists/*

# ✅ Correct paths (from your inspection)
COPY --from=build /build/llama.cpp/build/bin/llama-server /app/llama-server
COPY --from=build /build/llama.cpp/build/bin/rpc-server   /app/rpc-server

EXPOSE 8080 50052
