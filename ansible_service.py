import os
import json
import yaml
import tempfile
import subprocess
import logging
from datetime import datetime
from models import DeploymentExecution, HetznerServer, DeploymentScript
from app import db

class AnsibleService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.temp_dir = tempfile.mkdtemp(prefix='ansible_')
    
    def execute_deployment(self, server_id, script_id, user_id, variables=None):
        """Execute an Ansible deployment on a server"""
        try:
            # Get server and script
            server = HetznerServer.query.get(server_id)
            script = DeploymentScript.query.get(script_id)
            
            if not server or not script:
                raise ValueError("Server or script not found")
            
            if not server.public_ip:
                raise ValueError("Server does not have a public IP address")
            
            # Create deployment execution record
            execution = DeploymentExecution()
            execution.server_id = server_id
            execution.script_id = script_id
            execution.executed_by = user_id
            execution.status = 'pending'
            execution.execution_variables = json.dumps(variables or {})
            
            db.session.add(execution)
            db.session.commit()
            
            # Update server deployment status
            server.deployment_status = 'deploying'
            server.last_deployment = datetime.utcnow()
            db.session.commit()
            
            # Execute Ansible playbook
            result = self._run_ansible_playbook(
                server=server,
                script=script,
                execution=execution,
                variables=variables or {}
            )
            
            # Update execution record with results
            execution.status = 'completed' if result['success'] else 'failed'
            execution.completed_at = datetime.utcnow()
            execution.ansible_output = result.get('output', '')
            execution.error_log = result.get('error', '')
            execution.exit_code = result.get('exit_code', 0)
            
            # Update server deployment status
            server.deployment_status = 'deployed' if result['success'] else 'failed'
            server.deployment_log = result.get('output', '')
            
            # Update script execution count
            script.execution_count += 1
            script.last_executed = datetime.utcnow()
            
            db.session.commit()
            
            return {
                'success': result['success'],
                'execution_id': execution.execution_id,
                'output': result.get('output', ''),
                'error': result.get('error', '')
            }
            
        except Exception as e:
            self.logger.error(f"Error executing deployment: {str(e)}")
            
            # Update records to reflect failure
            if 'execution' in locals():
                execution.status = 'failed'
                execution.error_log = str(e)
                execution.completed_at = datetime.utcnow()
            
            if 'server' in locals():
                server.deployment_status = 'failed'
                server.deployment_log = str(e)
            
            db.session.commit()
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def _run_ansible_playbook(self, server, script, execution, variables):
        """Run the actual Ansible playbook"""
        try:
            # Create temporary files
            playbook_path = os.path.join(self.temp_dir, f'playbook_{execution.execution_id}.yml')
            inventory_path = os.path.join(self.temp_dir, f'inventory_{execution.execution_id}')
            vars_path = os.path.join(self.temp_dir, f'vars_{execution.execution_id}.json')
            
            # Write playbook to file
            with open(playbook_path, 'w') as f:
                f.write(script.ansible_playbook)
            
            # Create inventory file
            inventory_content = f"""[servers]
{server.name} ansible_host={server.public_ip} ansible_user=root ansible_ssh_private_key_file=~/.ssh/id_rsa
"""
            
            with open(inventory_path, 'w') as f:
                f.write(inventory_content)
            
            # Merge script variables with execution variables
            all_variables = {}
            if script.variables:
                try:
                    all_variables.update(json.loads(script.variables))
                except json.JSONDecodeError:
                    self.logger.warning(f"Invalid JSON in script variables for script {script.id}")
            
            all_variables.update(variables)
            all_variables.update({
                'server_name': server.name,
                'server_ip': server.public_ip,
                'server_type': server.server_type,
                'deployment_id': execution.execution_id
            })
            
            # Write variables to file
            with open(vars_path, 'w') as f:
                json.dump(all_variables, f, indent=2)
            
            # Construct ansible-playbook command
            cmd = [
                'ansible-playbook',
                '-i', inventory_path,
                '-e', f'@{vars_path}',
                '--ssh-extra-args', '-o StrictHostKeyChecking=no',
                playbook_path
            ]
            
            self.logger.info(f"Executing Ansible command: {' '.join(cmd)}")
            
            # Execute the playbook
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )
            
            # Clean up temporary files
            self._cleanup_temp_files([playbook_path, inventory_path, vars_path])
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr,
                'exit_code': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"Ansible playbook execution timed out for execution {execution.execution_id}")
            return {
                'success': False,
                'error': 'Playbook execution timed out (30 minutes)',
                'exit_code': -1
            }
        except Exception as e:
            self.logger.error(f"Error running Ansible playbook: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'exit_code': -1
            }
    
    def _cleanup_temp_files(self, file_paths):
        """Clean up temporary files"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                self.logger.warning(f"Could not remove temp file {file_path}: {str(e)}")
    
    def validate_playbook(self, playbook_content):
        """Validate Ansible playbook syntax"""
        try:
            # Parse YAML
            yaml.safe_load(playbook_content)
            
            # Create temporary playbook file
            temp_playbook = os.path.join(self.temp_dir, 'temp_validate.yml')
            with open(temp_playbook, 'w') as f:
                f.write(playbook_content)
            
            # Run ansible-playbook syntax check
            result = subprocess.run(
                ['ansible-playbook', '--syntax-check', temp_playbook],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Clean up
            if os.path.exists(temp_playbook):
                os.remove(temp_playbook)
            
            return {
                'valid': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }
            
        except yaml.YAMLError as e:
            return {
                'valid': False,
                'error': f'YAML syntax error: {str(e)}'
            }
        except Exception as e:
            return {
                'valid': False,
                'error': f'Validation error: {str(e)}'
            }
    
    def get_execution_status(self, execution_id):
        """Get status of a deployment execution"""
        execution = DeploymentExecution.query.filter_by(execution_id=execution_id).first()
        if not execution:
            return None
        
        return {
            'execution_id': execution.execution_id,
            'status': execution.status,
            'started_at': execution.started_at,
            'completed_at': execution.completed_at,
            'server_name': execution.server.name,
            'script_name': execution.script.name,
            'executor': execution.executor.username,
            'output': execution.ansible_output,
            'error': execution.error_log,
            'exit_code': execution.exit_code
        }
    
    def get_sample_playbooks(self):
        """Get sample Ansible playbooks for common tasks"""
        return {
            'nginx_setup': {
                'name': 'Install and Configure Nginx',
                'description': 'Installs Nginx web server and starts the service',
                'playbook': '''---
- name: Install and configure Nginx
  hosts: servers
  become: yes
  tasks:
    - name: Update package cache
      apt:
        update_cache: yes
      when: ansible_os_family == "Debian"
    
    - name: Install Nginx
      package:
        name: nginx
        state: present
    
    - name: Start and enable Nginx
      systemd:
        name: nginx
        state: started
        enabled: yes
    
    - name: Configure firewall for HTTP/HTTPS
      ufw:
        rule: allow
        port: "{{ item }}"
      with_items:
        - "80"
        - "443"
      when: ansible_os_family == "Debian"
''',
                'variables': {
                    'nginx_user': 'www-data',
                    'nginx_group': 'www-data'
                }
            },
            'docker_setup': {
                'name': 'Install Docker',
                'description': 'Installs Docker CE and Docker Compose',
                'playbook': '''---
- name: Install Docker
  hosts: servers
  become: yes
  tasks:
    - name: Update package cache
      apt:
        update_cache: yes
      when: ansible_os_family == "Debian"
    
    - name: Install prerequisites
      apt:
        name:
          - apt-transport-https
          - ca-certificates
          - curl
          - gnupg
          - lsb-release
        state: present
      when: ansible_os_family == "Debian"
    
    - name: Add Docker GPG key
      apt_key:
        url: https://download.docker.com/linux/ubuntu/gpg
        state: present
      when: ansible_os_family == "Debian"
    
    - name: Add Docker repository
      apt_repository:
        repo: deb https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} stable
        state: present
      when: ansible_os_family == "Debian"
    
    - name: Install Docker CE
      apt:
        name:
          - docker-ce
          - docker-ce-cli
          - containerd.io
          - docker-compose-plugin
        state: present
        update_cache: yes
      when: ansible_os_family == "Debian"
    
    - name: Start and enable Docker
      systemd:
        name: docker
        state: started
        enabled: yes
    
    - name: Add user to docker group
      user:
        name: "{{ ansible_user }}"
        groups: docker
        append: yes
''',
                'variables': {
                    'docker_users': ['root']
                }
            },
            'system_update': {
                'name': 'System Update and Security',
                'description': 'Updates system packages and applies security patches',
                'playbook': '''---
- name: System update and security hardening
  hosts: servers
  become: yes
  tasks:
    - name: Update package cache
      apt:
        update_cache: yes
      when: ansible_os_family == "Debian"
    
    - name: Upgrade all packages
      apt:
        upgrade: dist
        autoremove: yes
        autoclean: yes
      when: ansible_os_family == "Debian"
    
    - name: Install security updates
      apt:
        name: "*"
        state: latest
        only_upgrade: yes
      when: ansible_os_family == "Debian"
    
    - name: Install fail2ban
      apt:
        name: fail2ban
        state: present
      when: ansible_os_family == "Debian"
    
    - name: Configure UFW firewall
      ufw:
        state: enabled
        policy: deny
        direction: incoming
      when: ansible_os_family == "Debian"
    
    - name: Allow SSH
      ufw:
        rule: allow
        port: "22"
        proto: tcp
      when: ansible_os_family == "Debian"
    
    - name: Reboot if required
      reboot:
        msg: "Reboot initiated by Ansible for system updates"
      when: ansible_reboot_required is defined and ansible_reboot_required
''',
                'variables': {
                    'auto_reboot': True
                }
            }
        }