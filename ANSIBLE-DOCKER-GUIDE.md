# Running Ansible on Windows using Docker

Since Ansible doesn't run natively on Windows, we'll use Docker to run Ansible commands.

## Prerequisites

1. **Docker Desktop** - Download and install from https://www.docker.com/products/docker-desktop/
2. **SSH Key** - Make sure your SSH key is in `%USERPROFILE%\.ssh\id_rsa`

## Quick Start

### 1. First, check if Docker is running:
```cmd
docker --version
```

### 2. Build and test the Ansible container:
```cmd
ansible-docker.bat ping
```

### 3. Full deployment:
```cmd
ansible-docker.bat deploy
```

## Available Commands

```cmd
# Test connectivity to all VMs
ansible-docker.bat ping

# Setup Docker on all VMs
ansible-docker.bat setup

# Deploy all services
ansible-docker.bat deploy

# Check deployment status
ansible-docker.bat status

# Clean up (stop all containers)
ansible-docker.bat clean

# Interactive shell (for custom commands)
ansible-docker.bat shell
```

## Interactive Shell Usage

For custom Ansible commands, use the interactive shell:

```cmd
ansible-docker.bat shell
```

Then inside the container:
```bash
# Test connectivity
ansible all -i inventory.yml -m ping

# Run specific playbook
ansible-playbook -i inventory.yml setup-docker.yml

# Check specific service
ansible backend -i inventory.yml -m shell -a "docker ps"

# View logs
ansible postgres -i inventory.yml -m shell -a "docker logs postgres"
```

## Troubleshooting

### SSH Key Issues
If you get SSH authentication errors:
1. Make sure your SSH key is in `%USERPROFILE%\.ssh\id_rsa`
2. Test SSH manually: `ssh ubuntu@98.81.2.3`
3. Add your key to all VMs: `ssh-copy-id ubuntu@<vm-ip>`

### Docker Issues
- Make sure Docker Desktop is running
- Check if WSL2 backend is enabled in Docker Desktop settings

### Container Build Issues
```cmd
# Rebuild the container
docker-compose -f docker-compose-ansible.yml build --no-cache
```

## Manual Docker Commands

If you prefer running Docker commands directly:

```cmd
# Build the container
docker-compose -f docker-compose-ansible.yml build

# Run interactive shell
docker-compose -f docker-compose-ansible.yml run --rm ansible /bin/bash

# Run specific command
docker-compose -f docker-compose-ansible.yml run --rm ansible ansible all -i inventory.yml -m ping
```