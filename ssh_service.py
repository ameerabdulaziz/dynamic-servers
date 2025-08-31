"""
SSH Service for Remote Script Execution
Handles SSH connections and remote script execution on servers
"""

import paramiko
import io
import logging
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class SSHService:
    def __init__(self):
        self.client = None
    
    def test_connection(self, server):
        """Test SSH connection to a server"""
        try:
            with self._get_ssh_client(server) as client:
                if client:
                    # Simple test command
                    stdin, stdout, stderr = client.exec_command('echo "SSH connection test"')
                    output = stdout.read().decode().strip()
                    if output == "SSH connection test":
                        return True, "Connection successful"
                    else:
                        return False, "Unexpected response from server"
                else:
                    return False, "Failed to establish SSH connection"
        except Exception as e:
            logger.error(f"SSH connection test failed for {server.name}: {str(e)}")
            return False, str(e)
    
    def execute_script(self, server, script_content, timeout=300):
        """Execute a script on a remote server via SSH"""
        try:
            with self._get_ssh_client(server) as client:
                if not client:
                    return False, "Failed to establish SSH connection", "Connection failed"
                
                # Create a temporary script file on the remote server
                script_filename = f"/tmp/deploy_script_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sh"
                
                # Upload the script content
                stdin, stdout, stderr = client.exec_command(f'cat > {script_filename}')
                stdin.write(script_content)
                stdin.close()
                
                # Make the script executable
                client.exec_command(f'chmod +x {script_filename}')
                
                # Execute the script
                command = f'{script_filename}'
                stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
                
                # Wait for command to complete and get output
                stdout.channel.settimeout(timeout)
                stderr.channel.settimeout(timeout)
                
                output = stdout.read().decode('utf-8')
                error_output = stderr.read().decode('utf-8')
                exit_code = stdout.channel.recv_exit_status()
                
                # Clean up the temporary script
                client.exec_command(f'rm -f {script_filename}')
                
                success = exit_code == 0
                return success, output, error_output
                
        except paramiko.SSHException as e:
            logger.error(f"SSH error executing script on {server.name}: {str(e)}")
            return False, "", f"SSH error: {str(e)}"
        except Exception as e:
            logger.error(f"Error executing script on {server.name}: {str(e)}")
            return False, "", f"Execution error: {str(e)}"
    
    def execute_command(self, server, command, timeout=60):
        """Execute a single command on a remote server"""
        try:
            with self._get_ssh_client(server) as client:
                if not client:
                    return False, "Failed to establish SSH connection", "Connection failed"
                
                stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
                
                output = stdout.read().decode('utf-8')
                error_output = stderr.read().decode('utf-8')
                exit_code = stdout.channel.recv_exit_status()
                
                success = exit_code == 0
                return success, output, error_output
                
        except Exception as e:
            logger.error(f"Error executing command on {server.name}: {str(e)}")
            return False, "", f"Command execution error: {str(e)}"
    
    def download_file(self, server, remote_path, local_path):
        """Download a file from remote server to local system using SFTP"""
        try:
            with self._get_ssh_client(server) as client:
                if not client:
                    logger.error(f"Failed to establish SSH connection to {server.name}")
                    return False
                
                # Create SFTP client
                sftp = client.open_sftp()
                
                # Download the file
                sftp.get(remote_path, local_path)
                sftp.close()
                
                logger.info(f"Successfully downloaded {remote_path} from {server.name} to {local_path}")
                return True
                
        except paramiko.SSHException as e:
            logger.error(f"SSH error downloading file from {server.name}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error downloading file from {server.name}: {str(e)}")
            return False
    
    def get_latest_backup_file(self, server, backup_dir="/home/dynamic/nova-hr-docker/mssql/backup/"):
        """Get the latest backup file from the remote backup directory"""
        try:
            with self._get_ssh_client(server) as client:
                if not client:
                    return None
                
                # Find the latest backup file
                command = f"ls -t {backup_dir}*.sql | head -n 1"
                stdin, stdout, stderr = client.exec_command(command)
                output = stdout.read().decode('utf-8').strip()
                error_output = stderr.read().decode('utf-8')
                exit_code = stdout.channel.recv_exit_status()
                
                if exit_code == 0 and output:
                    return output
                else:
                    logger.error(f"No backup files found in {backup_dir} on {server.name}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error finding latest backup file: {str(e)}")
            return None
    
    @contextmanager
    def _get_ssh_client(self, server):
        """Create and configure SSH client for a server"""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # Configure connection parameters using project SSH settings
            project = server.project
            if not project:
                yield None
                return
                
            connect_kwargs = {
                'hostname': server.public_ip,
                'port': project.ssh_port or 22,
                'username': project.ssh_username or 'root',
                'timeout': 30
            }
            
            # Use private key from project if available
            if project.ssh_private_key:
                try:
                    key_file = io.StringIO(project.ssh_private_key)
                    private_key = paramiko.RSAKey.from_private_key(
                        key_file, 
                        password=project.ssh_key_passphrase
                    )
                    connect_kwargs['pkey'] = private_key
                except Exception as key_error:
                    # Try DSA key if RSA fails
                    try:
                        key_file = io.StringIO(project.ssh_private_key)
                        private_key = paramiko.DSSKey.from_private_key(
                            key_file, 
                            password=project.ssh_key_passphrase
                        )
                        connect_kwargs['pkey'] = private_key
                    except Exception:
                        # Try ECDSA key
                        try:
                            key_file = io.StringIO(project.ssh_private_key)
                            private_key = paramiko.ECDSAKey.from_private_key(
                                key_file, 
                                password=project.ssh_key_passphrase
                            )
                            connect_kwargs['pkey'] = private_key
                        except Exception:
                            # Try Ed25519 key
                            try:
                                key_file = io.StringIO(project.ssh_private_key)
                                private_key = paramiko.Ed25519Key.from_private_key(
                                    key_file, 
                                    password=project.ssh_key_passphrase
                                )
                                connect_kwargs['pkey'] = private_key
                            except Exception as final_error:
                                logger.error(f"Could not load SSH key for {server.name}: {final_error}")
                                yield None
                                return
            else:
                # No private key provided - this might fail for most servers
                logger.warning(f"No SSH private key configured for server {server.name}")
                # Could try password authentication here if implemented
                yield None
                return
            
            # Connect to the server
            client.connect(**connect_kwargs)
            yield client
            
        except Exception as e:
            logger.error(f"SSH connection failed for {server.name}: {str(e)}")
            yield None
        finally:
            try:
                client.close()
            except:
                pass

def get_default_deploy_script():
    """Returns the command to execute the Nova HR Docker deployment script"""
    return "cd /home/dynamic/nova-hr-docker && ./deploy.sh"

def get_default_backup_script():
    """Returns the command to execute the Nova HR Docker backup script"""
    return "cd /home/dynamic/nova-hr-docker && docker compose exec backup ./usr/src/app/backup-db.sh"

def get_nova_hr_script_content():
    """Returns the Nova HR Docker deployment script content for reference"""
    return """#!/bin/bash
# Nova HR Docker Deployment Script
# This script handles the deployment of Nova HR application

echo "Starting Nova HR Docker deployment..."
echo "Timestamp: $(date)"
echo "Working directory: $(pwd)"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose is not available"
    exit 1
fi

# Navigate to Nova HR directory
if [ -d "/home/dynamic/nova-hr-docker" ]; then
    cd /home/dynamic/nova-hr-docker
else
    echo "Error: Nova HR Docker directory not found at /home/dynamic/nova-hr-docker"
    exit 1
fi

echo "Step 1: Pulling latest Docker images..."
docker-compose pull || docker compose pull

echo "Step 2: Stopping existing containers..."
docker-compose down || docker compose down

echo "Step 3: Starting new containers..."
docker-compose up -d || docker compose up -d

echo "Step 4: Waiting for services to be ready..."
sleep 10

echo "Step 5: Checking container status..."
docker-compose ps || docker compose ps

echo "Step 6: Running any necessary migrations..."
# Add migration commands here if needed
# docker-compose exec web python manage.py migrate

echo "Step 7: Clearing application cache..."
# Add cache clearing commands here if needed

echo "Nova HR Docker deployment completed successfully!"
echo "Deployment finished at: $(date)"

# Return success exit code
exit 0
"""