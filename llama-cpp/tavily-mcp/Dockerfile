# -------- Builder stage --------
FROM node:22-alpine AS tavily-mcp-builder

COPY . /app

WORKDIR /app

# Copy dependency manifests
COPY package*.json ./

# Install all deps (including dev deps needed for build)
RUN npm ci

# Copy source
COPY . .

# Build (adjust if your build script differs)
RUN npm run build

# -------- Runtime stage --------
FROM node:22-alpine

WORKDIR /app

# Copy built artifacts + package.json only
COPY --from=tavily-mcp-builder /app/build /app/build
COPY --from=tavily-mcp-builder /app/package*.json ./

# Install prod deps only
RUN npm ci --ignore-scripts --omit=dev \
    && npm install -g supergateway

ENV NODE_ENV=production
ENV TAVILY_API_KEY=""

EXPOSE 8000

# Streamable HTTP mode: /mcp endpoint + healthz for K8s probes
CMD ["supergateway", \
     "--stdio", "./build/index.js", \
     "--outputTransport", "streamableHttp", \
     "--port", "8000", \
     "--host", "0.0.0.0", \
     "--cors", \
     "--healthEndpoint", "/healthz"]
