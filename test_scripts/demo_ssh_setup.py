#!/usr/bin/env python3
"""
Demo script to configure SSH access for testing
This will set up SSH configuration for the first available server
"""

import sys
import os
sys.path.append('.')

from app import app, db
from models import HetznerServer
from datetime import datetime

# Sample SSH private key (this is just for demo purposes)
DEMO_SSH_KEY = """-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAFwAAAAdzc2gtcn
NhAAAAAwEAAQAAAQEAwJKvdtLJwjlK8TQ1w6Qs3YkQVHhf9zMLpYtW4x3oGFI5lQRyU2YK
hMQ9+1FvW4hMzJk3yJ0TcqKnYXQ2pVVhKMjN7kYwF2YBqVLFxJ9yHJQoX0qQ7YkV1JzI
8wJKvdtLJwjlK8TQ1w6Qs3YkQVHhf9zMLpYtW4x3oGFI5lQRyU2YKhMQ9+1FvW4hMzJk3
yJ0TcqKnYXQ2pVVhKMjN7kYwF2YBqVLFxJ9yHJQoX0qQ7YkV1JzI8wJKvdtLJwjlK8TQ1
w6Qs3YkQVHhf9zMLpYtW4x3oGFI5lQRyU2YKhMQ9+1FvW4hMzJk3yJ0TcqKnYXQ2pVVh
KMjN7kYwF2YBqVLFxJ9yHJQoX0qQ7YkV1JzI8wJKvdtLJwjlK8TQ1w6Qs3YkQVHhf9zM
LpYtW4x3oGFI5lQRyU2YKhMQ9+1FvW4hMzJk3yJ0TcqKnYXQ2pVVhKMjN7kYwF2YBqVL
FxJ9yHJQoX0qQ7YkV1JzI8wJKvdtLJwjlK8TQ1w6Qs3YkQVHhf9zMLpYtW4x3oGFI5lQ
RyU2YKhMQ9+1FvW4hMzJk3yJ0TcqKnYXQ2pVVhKMjN7kYwF2YBqVLFxJ9yHJQoX0qQ7Y
kV1JzIAAAAAwEAAQAAAQEAwJKvdtLJwjlK8TQ1w6Qs3YkQVHhf9zMLpYtW4x3oGFI5lQRy
U2YKhMQ9+1FvW4hMzJk3yJ0TcqKnYXQ2pVVhKMjN7kYwF2YBqVLFxJ9yHJQoX0qQ7YkV
1JzI8wJKvdtLJwjlK8TQ1w6Qs3YkQVHhf9zMLpYtW4x3oGFI5lQRyU2YKhMQ9+1FvW4h
MzJk3yJ0TcqKnYXQ2pVVhKMjN7kYwF2YBqVLFxJ9yHJQoX0qQ7YkV1JzI8wJKvdtLJwj
lK8TQ1w6Qs3YkQVHhf9zMLpYtW4x3oGFI5lQRyU2YKhMQ9+1FvW4hMzJk3yJ0TcqKnYX
Q2pVVhKMjN7kYwF2YBqVLFxJ9yHJQoX0qQ7YkV1JzI8wJKvdtLJwjlK8TQ1w6Qs3YkQV
Hhf9zMLpYtW4x3oGFI5lQRyU2YKhMQ9+1FvW4hMzJk3yJ0TcqKnYXQ2pVVhKMjN7kYwF
2YBqVLFxJ9yHJQoX0qQ7YkV1JzI8wJKvdtLJwjlK8TQ1w6Qs3YkQVHhf9zMLpYtW4x3o
GFI5lQRyU2YKhMQ9+1FvW4hMzJk3yJ0TcqKnYXQ2pVVhKMjN7kYwF2YBqVLFxJ9yHJQo
X0qQ7YkV1JzI8wJKvdtLJwjlK8TQ1w6Qs3YkQVHhf9zMLpYtW4x3oGFI5lQRyU2YKhMQ
9+1FvW4hMzJk3yJ0TcqKnYXQ2pVVhKMjN7kYwF2YBqVLFxJ9yHJQoX0qQ7YkV1JzI8wJ
KvdtLJwjlK8TQ1w6Qs3YkQVHhf9zMLpYtW4x3oGFI5lQRyU2YKhMQ9+1FvW4hMzJk3yJ
0TcqKnYXQ2pVVhKMjN7kYwF2YBqVLFxJ9yHJQoX0qQ7YkV1JzI8wJKvdtLJwjlK8TQ1w
6Qs3YkQVHhf9zMLpYtW4x3oGFI5lQRyU2YKhMQ9+1FvW4hMzJk3yJ0TcqKnYXQ2pVVh
KMjN7kYwF2YBqVLFxJ9yHJQoX0qQ7YkV1JzI8wJKvdtLJwjlK8TQ1w6Qs3YkQVHhf9zM
LpYtW4x3oGFI5lQRyU2YKhMQ9+1FvW4hMzJk3yJ0TcqKnYXQ2pVVhKMjN7kYwF2YBqVL
FxJ9yHJQoX0qQ7YkV1JzI=
-----END OPENSSH PRIVATE KEY-----"""

def configure_demo_ssh():
    with app.app_context():
        # Get the first server
        server = HetznerServer.query.first()
        if not server:
            print("No servers found")
            return
            
        # Get the project for this server
        project = server.project
        if not project:
            print(f"Server {server.name} has no associated project")
            return
        
        print(f"Configuring SSH for project: {project.name} (affects server: {server.name})")
        
        # Configure SSH settings at project level
        project.ssh_username = 'root'  # Common default
        project.ssh_port = 22
        project.ssh_private_key = DEMO_SSH_KEY
        project.ssh_connection_tested = False  # Will test after configuration
        
        db.session.commit()
        print("SSH configuration saved at project level")
        
        # Test SSH connection
        from ssh_service import SSHService
        ssh_service = SSHService()
        
        try:
            success, message = ssh_service.test_connection(server)
            if success:
                project.ssh_connection_tested = True
                project.ssh_last_test = datetime.utcnow()
                db.session.commit()
                print(f"SSH connection test: SUCCESS - {message}")
            else:
                print(f"SSH connection test: FAILED - {message}")
        except Exception as e:
            print(f"SSH connection test: ERROR - {str(e)}")

if __name__ == '__main__':
    configure_demo_ssh()