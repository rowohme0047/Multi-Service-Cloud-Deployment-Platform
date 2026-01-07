#!/usr/bin/env python3
"""
DMAP Application Deployment Script
Dynamically updates inventory and runs Ansible deployment
"""

import os
import sys
import yaml
import subprocess
import argparse
import json
from typing import Dict, List

class DMAPDeployer:
    def __init__(self):
        self.workspace_dir = os.path.dirname(os.path.abspath(__file__))
        self.inventory_file = os.path.join(self.workspace_dir, 'inventory.yml')
        self.ansible_playbook = os.path.join(self.workspace_dir, 'deploy-services.yml')
        
    def check_container_exists(self) -> bool:
        """
        Check if ansible-control Docker container exists
        
        Returns:
            bool: True if container exists, False otherwise
        """
        try:
            cmd = ['docker', 'images', '-q', 'ansible-control']
            result = subprocess.run(cmd, capture_output=True, text=True)
            return bool(result.stdout.strip())
        except Exception:
            return False
    
    def check_docker_on_vms(self, vm_config: Dict[str, List[str]]) -> bool:
        """
        Check Docker installation on all VMs before proceeding
        
        Args:
            vm_config (dict): Dictionary with VM configuration
            
        Returns:
            bool: True if Docker is available on all VMs, False otherwise
        """
        print("Checking Docker installation on all VMs...")
        
        try:
            cmd = [
                'docker', 'run', '-it', '--rm',
                '-v', f'{self.workspace_dir}:/ansible',
                '-v', f'{os.path.expanduser("~")}/.ssh:/tmp/ssh:ro',
                '--user', 'root',
                'ansible-control',
                'bash', '-c',
                'cp -r /tmp/ssh /root/.ssh && chmod 700 /root/.ssh && chmod 600 /root/.ssh/* 2>/dev/null || true && ansible all -i inventory.yml -m shell -a "docker --version && docker compose version"'
            ]
            
            result = subprocess.run(cmd, cwd=self.workspace_dir)
            
            if result.returncode == 0:
                print("Docker is available on all VMs!")
                return True
            else:
                print("Docker is not available on one or more VMs")
                return False
                
        except Exception as e:
            print(f"Error checking Docker on VMs: {e}")
            return False
    
    def build_ansible_container(self) -> bool:
        """
        Build the Docker Ansible container if it doesn't exist
        
        Returns:
            bool: True if build successful or already exists, False otherwise
        """
        # Check if container already exists
        if self.check_container_exists():
            print(" Docker Ansible container already exists!")
            return True
            
        print("Building Docker Ansible container...")
        
        try:
            # Show build progress
            cmd = ['docker', 'build', '-t', 'ansible-control', '.']
            
            result = subprocess.run(cmd, cwd=self.workspace_dir)
            
            if result.returncode == 0:
                print("Docker Ansible container built successfully!")
                return True
            else:
                print(f" Container build failed with exit code: {result.returncode}")
                return False
                
        except Exception as e:
            print(f" Error building container: {e}")
            return False
        
    def update_inventory(self, vm_config: Dict[str, List[str]]) -> bool:
        """
        Update inventory.yml with provided VM configuration
        
        Args:
            vm_config (dict): Dictionary with VM names as keys and [IP, username, service] as values
                             Example: {"vm1": ["3.81.234.63", "ubuntu", "postgres"]}
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Parse VM configuration to extract service mappings
            service_to_vm = {}
            for vm_name, (ip, username, service) in vm_config.items():
                service_to_vm[service] = {
                    'vm_name': vm_name,
                    'ip': ip,
                    'username': username
                }
            
            # Define the inventory structure
            inventory = {
                'all': {
                    'children': {
                        'backend': {
                            'hosts': {
                                service_to_vm['backend']['vm_name']: {
                                    'ansible_host': service_to_vm['backend']['ip'],
                                    'ansible_user': service_to_vm['backend']['username']
                                }
                            }
                        },
                        'postgres': {
                            'hosts': {
                                service_to_vm['postgres']['vm_name']: {
                                    'ansible_host': service_to_vm['postgres']['ip'],
                                    'ansible_user': service_to_vm['postgres']['username']
                                }
                            }
                        },
                        'neo4j': {
                            'hosts': {
                                service_to_vm['neo4j']['vm_name']: {
                                    'ansible_host': service_to_vm['neo4j']['ip'],
                                    'ansible_user': service_to_vm['neo4j']['username']
                                }
                            }
                        },
                        'kafka': {
                            'hosts': {
                                service_to_vm['kafka']['vm_name']: {
                                    'ansible_host': service_to_vm['kafka']['ip'],
                                    'ansible_user': service_to_vm['kafka']['username']
                                }
                            }
                        }
                    },
                    'vars': {
                        'ansible_ssh_private_key_file': '~/.ssh/id_rsa',
                        'ansible_ssh_common_args': '-o StrictHostKeyChecking=no',
                        'docker_registry': 'ngdmapo',
                        'docker_repo': 'dmap_app_modernization',
                        'docker_hub_username': "{{ lookup('env', 'DOCKER_HUB_USERNAME') | default('ngdmapo') }}",
                        'docker_hub_password': "{{ lookup('env', 'DOCKER_HUB_PASSWORD') | default('') }}"
                    }
                }
            }
            
            # Write the inventory file
            with open(self.inventory_file, 'w') as f:
                yaml.dump(inventory, f, default_flow_style=False, indent=2)
            
            print(f"Updated inventory.yml with VM configuration:")
            for vm_name, (ip, username, service) in vm_config.items():
                print(f"   - {service.title()} VM ({vm_name}): {ip} (user: {username})")
            
            return True
            
        except Exception as e:
            print(f" Error updating inventory: {e}")
            return False
    
    def test_connectivity(self) -> bool:
        """
        Test SSH connectivity to all VMs using Ansible ping
        
        Returns:
            bool: True if all VMs are reachable, False otherwise
        """
        print("\nTesting connectivity to all VMs...")
        
        try:
            cmd = [
                'docker', 'run', '-it', '--rm',
                '-v', f'{self.workspace_dir}:/ansible',
                '-v', f'{os.path.expanduser("~")}/.ssh:/tmp/ssh:ro',
                '--user', 'root',
                'ansible-control',
                'bash', '-c',
                'cp -r /tmp/ssh /root/.ssh && chmod 700 /root/.ssh && chmod 600 /root/.ssh/* 2>/dev/null || true && ansible all -i inventory.yml -m ping'
            ]
            
            result = subprocess.run(cmd, cwd=self.workspace_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("All VMs are reachable!")
                return True
            else:
                print(f"Connectivity test failed:")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"Error testing connectivity: {e}")
            return False
    
    def run_deployment(self) -> bool:
        """
        Run the complete Ansible deployment
        
        Returns:
            bool: True if deployment successful, False otherwise
        """
        print("\nStarting deployment...")
        
        try:
            cmd = [
                'docker', 'run', '-it', '--rm',
                '-v', f'{self.workspace_dir}:/ansible',
                '-v', f'{os.path.expanduser("~")}/.ssh:/tmp/ssh:ro',
                '--user', 'root',
                'ansible-control',
                'bash', '-c',
                'cp -r /tmp/ssh /root/.ssh && chmod 700 /root/.ssh && chmod 600 /root/.ssh/* 2>/dev/null || true && ansible-playbook -i inventory.yml deploy-services.yml'
            ]
            
            result = subprocess.run(cmd, cwd=self.workspace_dir)
            
            if result.returncode == 0:
                print("Deployment completed successfully!")
                return True
            else:
                print(f" Deployment failed with exit code: {result.returncode}")
                return False
                
        except Exception as e:
            print(f"Error during deployment: {e}")
            return False
    
    def setup_docker(self) -> bool:
        """
        Setup Docker on all VMs using setup-docker.yml playbook
        
        Returns:
            bool: True if setup successful, False otherwise
        """
        print("Setting up Docker on all VMs...")
        
        try:
            cmd = [
                'docker', 'run', '-it', '--rm',
                '-v', f'{self.workspace_dir}:/ansible',
                '-v', f'{os.path.expanduser("~")}/.ssh:/tmp/ssh:ro',
                '--user', 'root',
                'ansible-control',
                'bash', '-c',
                'cp -r /tmp/ssh /root/.ssh && chmod 700 /root/.ssh && chmod 600 /root/.ssh/* 2>/dev/null || true && ansible-playbook -i inventory.yml setup-docker.yml'
            ]
            
            result = subprocess.run(cmd, cwd=self.workspace_dir)
            
            if result.returncode == 0:
                print("Docker setup completed successfully!")
                return True
            else:
                print(f"Docker setup failed with exit code: {result.returncode}")
                print("Docker setup failed. This is required for deployment.")
                return False
                
        except Exception as e:
            print(f"Error during Docker setup: {e}")
            return False
    
    def verify_deployment(self) -> bool:
        """
        Verify that all containers are running on their respective VMs
        
        Returns:
            bool: True if verification successful, False otherwise
        """
        print("\n🔍 Verifying deployment...")
        
        try:
            cmd = [
                'docker', 'run', '-it', '--rm',
                '-v', f'{self.workspace_dir}:/ansible',
                '-v', f'{os.path.expanduser("~")}/.ssh:/tmp/ssh:ro',
                '--user', 'root',
                'ansible-control',
                'bash', '-c',
                'cp -r /tmp/ssh /root/.ssh && chmod 700 /root/.ssh && chmod 600 /root/.ssh/* 2>/dev/null || true && ansible all -i inventory.yml -a "docker ps --format \'table {{.Names}}\t{{.Status}}\t{{.Ports}}\'"'
            ]
            
            result = subprocess.run(cmd, cwd=self.workspace_dir)
            
            if result.returncode == 0:
                print("Deployment verification completed!")
                return True
            else:
                print(f"Verification failed with exit code: {result.returncode}")
                return False
                
        except Exception as e:
            print(f"Error during verification: {e}")
            return False
    
    def deploy(self, vm_config: Dict[str, List[str]], skip_connectivity_test: bool = False, setup_docker_first: bool = True) -> bool:
        """
        Complete deployment flow
        
        Args:
            vm_config (dict): Dictionary with VM configuration
                             Example: {"vm1": ["3.81.234.63", "ubuntu", "postgres"]}
            skip_connectivity_test (bool): Skip connectivity test if True
            setup_docker_first (bool): Setup Docker on VMs first if True
            
        Returns:
            bool: True if entire flow successful, False otherwise
        """
        print("DMAP Application Deployment Starting...")
        print("=" * 50)
        
        # Step 1: Build Docker Ansible container
        if not self.build_ansible_container():
            return False
        
        # Step 2: Update inventory
        if not self.update_inventory(vm_config):
            return False
        
        # Step 3: Test connectivity
        if not skip_connectivity_test:
            if not self.test_connectivity():
                return False
        
        # Step 4: Check Docker on VMs
        docker_available = self.check_docker_on_vms(vm_config)
        
        # Step 5: Setup Docker if needed
        if not docker_available and setup_docker_first:
            if not self.setup_docker():
                return False
        elif not docker_available and not setup_docker_first:
            print("Docker is not available on VMs and setup is skipped. Deployment may fail.")
        
        # Step 6: Run deployment
        if not self.run_deployment():
            return False
            
        # # Step 5: Verify deployment
        # if not self.verify_deployment():
        #     print("Verification failed, but deployment may still be successful.")
        
        print("\nDMAP Application Deployment Complete!")
        print("=" * 50)
        return True

    def setup_docker_only(self, vm_config: Dict[str, List[str]]) -> bool:
        """
        Setup Docker only (without deployment)
        
        Args:
            vm_config (dict): Dictionary with VM configuration
                             Example: {"vm1": ["3.81.234.63", "ubuntu", "postgres"]}
            
        Returns:
            bool: True if setup successful, False otherwise
        """
        print("Docker Setup Starting...")
        print("=" * 50)
        
        # Step 1: Build Docker Ansible container
        if not self.build_ansible_container():
            return False
        
        # Step 2: Update inventory
        if not self.update_inventory(vm_config):
            return False
        
        # Step 3: Test connectivity
        if not self.test_connectivity():
            return False
        
        # Step 4: Setup Docker
        if not self.setup_docker():
            return False
            
        print("\nDocker Setup Complete!")
        print("=" * 50)
        return True


def main():
    """Main function to handle command line arguments and run deployment"""
    
    parser = argparse.ArgumentParser(description='DMAP Application Deployment Script')
    parser.add_argument('--vm-config', help='JSON file with VM configuration in format: {"vm1": ["ip", "username", "service"]}')
    parser.add_argument('--skip-connectivity', action='store_true', help='Skip connectivity test')
    parser.add_argument('--skip-docker-setup', action='store_true', help='Skip Docker setup (assumes Docker is already installed)')
    parser.add_argument('--docker-setup-only', action='store_true', help='Only setup Docker without deploying services')
    
    args = parser.parse_args()
    
    deployer = DMAPDeployer()
    
    # Handle VM config file
    if args.vm_config:
        try:
            with open(args.vm_config, 'r') as f:
                vm_config = json.load(f)
        except Exception as e:
            print(f" Error reading VM config: {e}")
            return 1
    else:
        # Default configuration for backward compatibility
        vm_config = {
        "vm1": ["54.226.239.194", "ubuntu", "postgres"],
        "vm2": ["18.207.127.165", "ubuntu", "neo4j"],
        "vm3": ["3.83.229.79", "ubuntu", "kafka"],
        "vm4": ["54.167.120.93", "ubuntu", "backend"]
    }
 
        print("Using default VM configuration. Use --vm-config to specify custom configuration.")
    
    # Run deployment or Docker setup only
    if args.docker_setup_only:
        success = deployer.setup_docker_only(vm_config)
    else:
        success = deployer.deploy(vm_config, args.skip_connectivity, not args.skip_docker_setup)
    
    return 0 if success else 1


# Function that can be called by other services
def deploy_dmap_application(vm_config: Dict[str, List[str]]) -> bool:
    """
    Function that can be called by other services to deploy DMAP application
    
    Args:
        vm_config (dict): Dictionary with VM configuration
                         Example: {"vm1": ["3.81.234.63", "ubuntu", "postgres"]}
        
    Returns:
        bool: True if deployment successful, False otherwise
    """
    deployer = DMAPDeployer()
    
    return deployer.deploy(vm_config, skip_connectivity_test=False)


if __name__ == "__main__":
    sys.exit(main())