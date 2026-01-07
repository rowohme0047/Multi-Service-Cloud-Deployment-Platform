FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    openssh-client \
    sshpass \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Ansible and dependencies
RUN pip install --no-cache-dir \
    ansible \
    docker \
    pyyaml \
    jinja2 \
    cryptography

# Create ansible user
RUN useradd -m -s /bin/bash ansible

# Set working directory
WORKDIR /ansible

# Copy deployment files
COPY . /ansible/

# Set permissions
RUN chown -R ansible:ansible /ansible

# Switch to ansible user
USER ansible

# Default command
CMD ["/bin/bash"]