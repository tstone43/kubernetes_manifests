FROM codercom/code-server:latest

# Switch to root for tool installation
USER root

# ---- Base utilities ----
RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    unzip \
    git \
    python3 \
    python3-venv \
    python3-pip \
    openssh-client \
    jq \
    && rm -rf /var/lib/apt/lists/*
    
# ---- kubectl ----
RUN curl -LO "https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && chmod +x kubectl \
    && mv kubectl /usr/local/bin/kubectl

# ---- Terraform ----
ARG TERRAFORM_VERSION=1.7.5
RUN curl -LO https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip \
    && unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip \
    && mv terraform /usr/local/bin/terraform \
    && rm terraform_${TERRAFORM_VERSION}_linux_amd64.zip

# ---- Ansible ----
# ---- Ansible (PEP 668 compliant) ----
RUN python3 -m venv /opt/ansible-venv \
    && /opt/ansible-venv/bin/pip install --upgrade pip \
    && /opt/ansible-venv/bin/pip install \
        ansible \
        ansible-core \
        openshift \
        kubernetes

ENV PATH="/opt/ansible-venv/bin:$PATH"

# ---- Docker CLI (NOT Docker daemon) ----
RUN curl -fsSL https://get.docker.com | sh \
    && rm -rf /var/lib/apt/lists/*

# ---- Add coder user to docker group ----
RUN usermod -aG docker coder

# ---- Ensure permissions on home dir ----
RUN chown -R coder:coder /home/coder

# Switch back to coder user
USER coder

# Default working directory
WORKDIR /home/coder

# Expose code-server port
EXPOSE 8080