@echo off
REM Windows script to run Ansible commands through Docker container

setlocal enabledelayedexpansion

REM Colors for output
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "NC=[0m"

:print_status
echo %GREEN%[INFO]%NC% %~1
goto :eof

:print_error
echo %RED%[ERROR]%NC% %~1
goto :eof

:check_docker
call :print_status "Checking Docker..."
docker --version >nul 2>&1
if errorlevel 1 (
    call :print_error "Docker is not installed or not running. Please install Docker Desktop."
    exit /b 1
)
call :print_status "Docker is available"
goto :eof

:build_ansible_container
call :print_status "Building Ansible container..."
docker-compose -f docker-compose-ansible.yml build
if errorlevel 1 (
    call :print_error "Failed to build Ansible container"
    exit /b 1
)
call :print_status "Ansible container built successfully"
goto :eof

:run_ansible_command
set "cmd=%~1"
call :print_status "Running: %cmd%"
docker-compose -f docker-compose-ansible.yml run --rm ansible %cmd%
goto :eof

:main
call :print_status "DMAP Ansible Docker Runner"
echo ===============================

call :check_docker
call :build_ansible_container

if "%~1"=="" set "action=help"
if not "%~1"=="" set "action=%~1"

if "!action!"=="shell" (
    call :print_status "Starting interactive Ansible shell..."
    docker-compose -f docker-compose-ansible.yml run --rm ansible /bin/bash
) else if "!action!"=="ping" (
    call :run_ansible_command "ansible all -i inventory.yml -m ping"
) else if "!action!"=="setup" (
    call :run_ansible_command "ansible-playbook -i inventory.yml setup-docker.yml"
) else if "!action!"=="deploy" (
    call :run_ansible_command "ansible-playbook -i inventory.yml deploy-services.yml"
) else if "!action!"=="status" (
    call :run_ansible_command "ansible all -i inventory.yml -m shell -a 'docker ps --format \"table {{.Names}}\t{{.Status}}\t{{.Ports}}\"'"
) else if "!action!"=="clean" (
    call :run_ansible_command "ansible all -i inventory.yml -m shell -a 'docker stop $(docker ps -aq) || true'"
    call :run_ansible_command "ansible all -i inventory.yml -m shell -a 'docker rm $(docker ps -aq) || true'"
) else (
    echo Usage: %~nx0 [shell^|ping^|setup^|deploy^|status^|clean]
    echo.
    echo Commands:
    echo   shell  - Start interactive Ansible shell
    echo   ping   - Test connectivity to all VMs
    echo   setup  - Install Docker on all VMs
    echo   deploy - Deploy all services
    echo   status - Check deployment status
    echo   clean  - Stop and remove all containers
    exit /b 1
)

call :print_status "Operation completed!"
goto :eof

call :main %*