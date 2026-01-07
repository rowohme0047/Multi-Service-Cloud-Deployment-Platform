#Application Multi-VM Deployment

This repository contains the Ansible-based deployment solution for the Application across 4 VMs using Docker containers.

## Architecture Overview

The application is distributed across 4 VMs as follows:

- **VM1 ** - Postgres: 1 container
- **VM2 ** - Neo4j: 1 container  
- **VM3 ** - Kafka: 1 container
- **VM4 ** - Backend: 12 containers
  - Agent: 3 containers
  - GraphDB: 2 containers
  - S3: 1 container
  - Nginx: 1 container
  - DocumentGen: 1 container
  - Kafka OpenAI: 3 containers
  - AI Infra Provisioning: 1 container

## Prerequisites

### System Requirements
- **Control Machine**: Windows, Linux, or macOS
- **Target VMs**: Ubuntu 20.04+ with SSH access
- **Network**: All VMs must be able to communicate with each other

### Software Requirements
- Ansible 2.9+
- SSH client
- Python 3.6+

### Installation

#### Windows
```powershell
# Option 1: Using pip
pip install ansible

# Option 2: Using WSL2
wsl --install
# In WSL terminal:
sudo apt update && sudo apt install ansible
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ansible python3-pip
```

#### macOS
```bash
# Using Homebrew
brew install ansible

# Using pip
pip3 install ansible
```

## Configuration

### 1. SSH Key Setup
Ensure your SSH key is configured:
```bash
# Generate SSH key if you don't have one
ssh-keygen -t rsa -b 4096

# Copy to all VMs
ssh-copy-id ubuntu@3.81.234.63
ssh-copy-id ubuntu@54.224.159.62
ssh-copy-id ubuntu@54.196.81.150
ssh-copy-id ubuntu@98.81.2.3
```

### 2. Inventory Configuration
The `inventory.yml` file contains VM details. Update if needed:
```yaml
all:
  children:
    backend:
      hosts:
        vm4:
          ansible_host: 98.81.2.3
    postgres:
      hosts:
        vm1:
          ansible_host: 3.81.234.63
    neo4j:
      hosts:
        vm2:
          ansible_host: 54.224.159.62
    kafka:
      hosts:
        vm3:
          ansible_host: 54.196.81.150
```

## Deployment

### Quick Start (Recommended)

#### Windows
```cmd
deploy.bat deploy
```

#### Linux/macOS
```bash
chmod +x deploy.sh
./deploy.sh deploy
```

### Step-by-Step Deployment

#### 1. Check Prerequisites and Connectivity
```bash
# Linux/macOS
./deploy.sh check

# Windows
deploy.bat check
```

#### 2. Setup Docker on All VMs
```bash
# Linux/macOS
./deploy.sh setup

# Windows
deploy.bat setup
```

#### 3. Deploy Services
```bash
# Linux/macOS
./deploy.sh deploy

# Windows
deploy.bat deploy
```

### Manual Deployment (Alternative)

```bash
# 1. Test connectivity
ansible all -i inventory.yml -m ping

# 2. Setup Docker
ansible-playbook -i inventory.yml setup-docker.yml

# 3. Deploy services
ansible-playbook -i inventory.yml deploy-services.yml
```

## Service Management

### Check Deployment Status
```bash
# Linux/macOS
./deploy.sh status

# Windows
deploy.bat status
```

### Stop All Services
```bash
# Linux/macOS
./deploy.sh clean

# Windows
deploy.bat clean
```

### Restart Specific Service
```bash
# Restart backend services
ansible backend -i inventory.yml -m shell -a "cd /home/ubuntu/deployment && docker-compose restart"

# Restart postgres
ansible postgres -i inventory.yml -m shell -a "cd /home/ubuntu/deployment && docker-compose restart"
```

## Service URLs

After successful deployment, services will be available at:

- 🌐 **Web Interface (Nginx)**: http://98.81.2.3
- 📊 **S3 Storage**: http://98.81.2.3:9000
- 🗄️ **PostgreSQL**: postgresql://3.81.234.63:5432
- 🕸️ **Neo4j Browser**: http://54.224.159.62:7474
- 📨 **Kafka**: 54.196.81.150:9092

## Monitoring

### View Container Logs
```bash
# Backend services logs
ansible backend -i inventory.yml -m shell -a "docker logs nginx"
ansible backend -i inventory.yml -m shell -a "docker logs agent-1"

# Database logs
ansible postgres -i inventory.yml -m shell -a "docker logs postgres"
ansible neo4j -i inventory.yml -m shell -a "docker logs neo4j"
ansible kafka -i inventory.yml -m shell -a "docker logs kafka"
```

### View Container Status
```bash
ansible all -i inventory.yml -m shell -a "docker ps"
```

## Troubleshooting

### Common Issues

#### 1. SSH Connection Failed
```bash
# Test SSH connection manually
ssh ubuntu@98.81.2.3

# Check SSH key permissions
chmod 600 ~/.ssh/id_rsa
```

#### 2. Docker Permission Denied
```bash
# Add user to docker group (already handled in setup)
ansible all -i inventory.yml -m shell -a "sudo usermod -aG docker ubuntu"
```

#### 3. Container Not Starting
```bash
# Check logs
ansible backend -i inventory.yml -m shell -a "docker logs container_name"

# Check resources
ansible all -i inventory.yml -m shell -a "docker system df"
```

#### 4. Network Connectivity Issues
```bash
# Test inter-VM connectivity
ansible all -i inventory.yml -m shell -a "ping -c 3 3.81.234.63"
```

### Debug Mode
Run with verbose output:
```bash
ansible-playbook -i inventory.yml deploy-services.yml -vvv
```

## Security Considerations

1. **Firewall Rules**: Ensure proper security group configurations
2. **SSH Keys**: Use strong SSH keys and disable password authentication
3. **Container Security**: Regularly update images for security patches
4. **Network Segmentation**: Consider VPC/subnet isolation
5. **Secrets Management**: Use environment variables for sensitive data

## Environment Variables

Configure in respective docker-compose files:

### Backend Services
- `POSTGRES_HOST=3.81.234.63`
- `NEO4J_HOST=54.224.159.62`
- `KAFKA_HOST=54.196.81.150`

### Database Services
- `POSTGRES_DB=dmap_db`
- `POSTGRES_USER=dmap_user`
- `POSTGRES_PASSWORD=dmap_password`
- `NEO4J_AUTH=neo4j/dmap_password`

## Backup and Recovery

### Database Backups
```bash
# PostgreSQL backup
ansible postgres -i inventory.yml -m shell -a "docker exec postgres pg_dump -U dmap_user dmap_db > backup.sql"

# Neo4j backup
ansible neo4j -i inventory.yml -m shell -a "docker exec neo4j neo4j-admin backup --backup-dir=/backups"
```

## Scaling

### Horizontal Scaling
To add more instances:
1. Update `docker-compose-backend.yml` with additional containers
2. Run deployment again

### Vertical Scaling
Update resource limits in docker-compose files:
```yaml
services:
  service_name:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

## Contributing

1. Update configurations in respective files
2. Test changes with `./deploy.sh check`
3. Deploy with `./deploy.sh deploy`

## Support

For issues and questions:
1. Check logs using monitoring commands
2. Verify network connectivity
3. Review security group settings
4. Check VM resources and status
