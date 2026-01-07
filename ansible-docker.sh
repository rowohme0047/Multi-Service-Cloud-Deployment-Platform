#!/bin/bash

# Cross-platform script to run Ansible commands through Docker container

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_docker() {
    print_status "Checking Docker..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker."
        exit 1  
    fi
    
    print_status "Docker is available"
}

build_ansible_container() {
    print_status "Building Ansible container..."
    docker-compose -f docker-compose-ansible.yml build
    print_status "Ansible container built successfully"
}

run_ansible_command() {
    local cmd="$1"
    print_status "Running: $cmd"
    docker-compose -f docker-compose-ansible.yml run --rm ansible $cmd
}

main() {
    print_status "DMAP Ansible Docker Runner"
    echo "==============================="
    
    check_docker
    build_ansible_container
    
    case "${1:-help}" in
        "shell")
            print_status "Starting interactive Ansible shell..."
            docker-compose -f docker-compose-ansible.yml run --rm ansible /bin/bash
            ;;
        "ping")
            run_ansible_command "ansible all -i inventory.yml -m ping"
            ;;
        "setup")
            run_ansible_command "ansible-playbook -i inventory.yml setup-docker.yml"
            ;;
        "deploy")
            run_ansible_command "ansible-playbook -i inventory.yml deploy-services.yml"
            ;;
        "status")
            run_ansible_command "ansible all -i inventory.yml -m shell -a 'docker ps --format \"table {{.Names}}\t{{.Status}}\t{{.Ports}}\"'"
            ;;
        "clean")
            run_ansible_command "ansible all -i inventory.yml -m shell -a 'docker stop \$(docker ps -aq) || true'"
            run_ansible_command "ansible all -i inventory.yml -m shell -a 'docker rm \$(docker ps -aq) || true'"
            ;;
        *)
            echo "Usage: $0 {shell|ping|setup|deploy|status|clean}"
            echo ""
            echo "Commands:"
            echo "  shell  - Start interactive Ansible shell"
            echo "  ping   - Test connectivity to all VMs"
            echo "  setup  - Install Docker on all VMs"
            echo "  deploy - Deploy all services"
            echo "  status - Check deployment status"
            echo "  clean  - Stop and remove all containers"
            exit 1
            ;;
    esac
    
    print_status "Operation completed!"
}

main "$@"