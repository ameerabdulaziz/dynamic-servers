import random
import time
import os
import subprocess
from pathlib import Path
from datetime import datetime
import pytz
from flask import render_template, redirect, url_for, flash, request, jsonify, make_response, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from app import app, db
from models import User, UserRole, ServerRequest, Notification, HetznerServer, DeploymentScript, DeploymentExecution, ClientSubscription, DatabaseBackup, SystemUpdate, HetznerProject, UserProjectAccess, UserServerAccess
from forms import LoginForm, RegistrationForm, ServerRequestForm, EditProfileForm, AdminReviewForm, DeploymentScriptForm, ExecuteDeploymentForm, ServerManagementForm, SelfHostedServerForm
from hetzner_service import HetznerService
from godaddy_service import GoDaddyService
from ansible_service import AnsibleService
from ssh_service import SSHService, get_default_deploy_script, get_default_backup_script

def convert_to_cairo_timezone(utc_datetime):
    """Convert UTC datetime to Cairo timezone"""
    if utc_datetime is None:
        return None
    
    # Create UTC timezone object
    utc_tz = pytz.UTC
    
    # Create Cairo timezone object  
    cairo_tz = pytz.timezone('Africa/Cairo')
    
    # If the datetime is naive (no timezone info), assume it's UTC
    if utc_datetime.tzinfo is None:
        utc_datetime = utc_tz.localize(utc_datetime)
    
    # Convert to Cairo timezone
    cairo_datetime = utc_datetime.astimezone(cairo_tz)
    
    return cairo_datetime

def provision_server_and_dns(server_request: ServerRequest):
    """
    Provision a Hetzner server and configure DNS record automatically
    """
    try:
        app.logger.info(f"Starting server provisioning for request: {server_request.request_id}")
        
        # Update request status to deploying
        server_request.status = 'deploying'
        server_request.deployment_progress = 10
        db.session.commit()
        
        # Initialize Hetzner service with the project's API token
        if not server_request.project_id:
            return {'success': False, 'error': 'No project specified for server request'}
        
        hetzner_service = HetznerService(project_id=server_request.project_id)
        
        # Prepare server labels (sanitized for Hetzner Cloud requirements)
        def sanitize_label_value(value):
            """Sanitize label values to meet Hetzner requirements: a-z, 0-9, -, _"""
            if not value:
                return 'none'
            # Convert to lowercase and replace invalid characters
            sanitized = ''.join(c if c.isalnum() or c in '-_' else '-' for c in str(value).lower())
            # Remove consecutive dashes and trim
            sanitized = '-'.join(filter(None, sanitized.split('-')))
            return sanitized[:63]  # Max length is 63 characters
        
        labels = {
            'client': sanitize_label_value(server_request.client_name),
            'request-id': sanitize_label_value(server_request.request_id),
            'managed-by': 'dynamic-servers',
            'subdomain': sanitize_label_value(server_request.subdomain)
        }
        
        # Update progress
        server_request.deployment_progress = 20
        db.session.commit()
        
        # Create server in Hetzner Cloud
        creation_result = hetzner_service.create_server(
            name=server_request.server_name,
            server_type=server_request.server_type,
            image=server_request.operating_system,
            location='nbg1',  # Default location
            labels=labels
        )
        
        if not creation_result['success']:
            server_request.status = 'failed'
            server_request.deployment_notes = f"Server creation failed: {creation_result['error']}"
            db.session.commit()
            return creation_result
        
        # Update progress and get IP address
        server_ip = creation_result['ip_address']
        server_request.server_ip = server_ip
        server_request.deployment_progress = 60
        db.session.commit()
        
        app.logger.info(f"Server created successfully with IP: {server_ip}")
        
        # Configure DNS if base domain exists
        if server_request.project.base_domain and server_request.subdomain:
            app.logger.info(f"Configuring DNS for {server_request.subdomain}.{server_request.project.base_domain}")
            
            godaddy_service = GoDaddyService()
            dns_result = godaddy_service.add_dns_record(
                domain=server_request.project.base_domain,
                subdomain=server_request.subdomain,
                ip_address=server_ip
            )
            
            # Update progress
            server_request.deployment_progress = 80
            db.session.commit()
            
            if dns_result['success']:
                app.logger.info(f"DNS record created successfully: {server_request.subdomain}.{server_request.project.base_domain} -> {server_ip}")
                dns_message = f"DNS configured: {server_request.subdomain}.{server_request.project.base_domain}"
            else:
                app.logger.warning(f"DNS configuration failed: {dns_result['error']}")
                dns_message = f"DNS configuration failed: {dns_result['error']}"
        else:
            dns_message = "DNS configuration skipped (no base domain configured)"
            app.logger.info(dns_message)
        
        # Mark as successfully deployed
        server_request.status = 'deployed'
        server_request.deployment_progress = 100
        server_request.deployed_at = datetime.utcnow()
        server_request.deployment_notes = f"Server provisioned successfully. IP: {server_ip}. {dns_message}"
        
        # Create success notification
        notification = Notification()
        notification.user_id = server_request.user_id
        notification.title = 'Server Deployed Successfully'
        notification.message = f'Your server "{server_request.server_name}" has been deployed at {server_ip}'
        if server_request.project.base_domain:
            notification.message += f' and is accessible at {server_request.subdomain}.{server_request.project.base_domain}'
        notification.type = 'success'
        notification.request_id = server_request.id
        db.session.add(notification)
        
        db.session.commit()
        
        app.logger.info(f"Server provisioning completed successfully for request: {server_request.request_id}")
        
        return {
            'success': True,
            'server_ip': server_ip,
            'full_domain': f"{server_request.subdomain}.{server_request.project.base_domain}" if server_request.project.base_domain else None,
            'message': 'Server provisioned and DNS configured successfully'
        }
        
    except Exception as e:
        app.logger.error(f"Error in server provisioning: {e}")
        
        # Mark as failed
        server_request.status = 'failed'
        server_request.deployment_notes = f"Provisioning failed: {str(e)}"
        
        # Create failure notification
        notification = Notification()
        notification.user_id = server_request.user_id
        notification.title = 'Server Deployment Failed'
        notification.message = f'Server deployment for "{server_request.server_name}" failed: {str(e)}'
        notification.type = 'error'
        notification.request_id = server_request.id
        db.session.add(notification)
        
        db.session.commit()
        
        return {
            'success': False,
            'error': str(e)
        }

@app.route('/')
def index():
    if not current_user.is_authenticated:
        return render_template('index.html')
    
    # Main dashboard - redirect based on user role
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    elif current_user.is_technical_agent:
        return redirect(url_for('technical_dashboard'))
    elif current_user.is_sales_agent:
        return redirect(url_for('sales_dashboard'))
    
    # Fallback for any other roles
    return redirect(url_for('sales_dashboard'))

@app.route('/admin/backup-system')
@login_required
def create_system_backup():
    """Create and download our system's database backup"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Ensure backups directory exists
    backup_dir = Path("static/backups/system")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"system_database_{timestamp}.sql"
    backup_path = backup_dir / backup_filename
    
    try:
        # Create the backup using pg_dump
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            flash('Database URL not configured', 'danger')
            return redirect(url_for('admin_dashboard'))
        
        with open(backup_path, 'w') as backup_file:
            subprocess.run([
                'pg_dump', 
                database_url,
                '--no-owner',
                '--no-privileges'
            ], stdout=backup_file, check=True)
        
        # Get file size and save record to database
        file_size = backup_path.stat().st_size
        
        # Create backup record in database
        backup_record = DatabaseBackup()
        backup_record.server_id = None  # System backup
        backup_record.backup_type = 'system'
        backup_record.database_name = 'dynamic_servers'
        backup_record.file_path = str(backup_path)
        backup_record.file_size = file_size
        backup_record.status = 'completed'
        backup_record.initiated_by = current_user.id
        backup_record.started_at = datetime.now()
        backup_record.completed_at = datetime.now()
        
        db.session.add(backup_record)
        db.session.commit()
        
        flash(f'System database backup created successfully! Size: {file_size:,} bytes', 'success')
        
        # Return the file for download
        return send_from_directory('static/backups/system', backup_filename, as_attachment=True)
        
    except subprocess.CalledProcessError as e:
        flash(f'Failed to create backup: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))
    except Exception as e:
        flash(f'Unexpected error: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/backups')
@login_required
def list_all_backups():
    """List all available backups (system + server backups)"""
    if not current_user.is_admin and not current_user.is_technical_agent:
        flash('Access denied. Admin or Technical privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Get existing backup files from filesystem
    system_backups = []
    server_backups = []
    
    # Check for system backup files (admin only)
    if current_user.is_admin:
        system_backup_dir = Path("static/backups")
        if system_backup_dir.exists():
            for backup_file in system_backup_dir.glob("*.sql"):
                if backup_file.is_file():
                    stat = backup_file.stat()
                    system_backups.append({
                        'id': None,  # Use filename instead
                        'filename': backup_file.name,
                        'server_name': 'System Database',
                        'database_name': 'dynamic_servers',
                        'backup_type': 'system',
                        'size': stat.st_size,
                        'status': 'completed',
                        'created': datetime.fromtimestamp(stat.st_mtime),
                        'initiated_by': 'System',
                        'download_url': url_for('download_backup_file', filename=backup_file.name),
                        'file_exists': True
                    })
    
    # Check for server backup files organized by server name
    server_backup_root = Path("static/backups/servers")
    
    # Get list of accessible servers for permission filtering
    if not current_user.is_admin:
        accessible_servers = current_user.get_accessible_servers()
        accessible_server_names = [s.name for s in accessible_servers]
    
    if server_backup_root.exists():
        # Go through each server directory
        for server_dir in server_backup_root.iterdir():
            if server_dir.is_dir():
                server_name = server_dir.name
                
                # Skip servers that user doesn't have access to
                if not current_user.is_admin and server_name not in accessible_server_names:
                    continue
                # Find backup files in this server's directory (.bak files)
                for backup_file in server_dir.glob("*.bak"):
                    if backup_file.is_file():
                        stat = backup_file.stat()
                        # Parse database name from filename (e.g., ehaf_backup_2025-08-31_15-28.bak)
                        filename_parts = backup_file.name.split('_')
                        database_name = filename_parts[0] if filename_parts else 'main'
                        server_backups.append({
                            'id': None,  # Use server/filename path instead
                            'filename': backup_file.name,
                            'server_name': server_name,
                            'database_name': database_name,
                            'backup_type': 'server',
                            'size': stat.st_size,
                            'status': 'completed',
                            'created': datetime.fromtimestamp(stat.st_mtime),
                            'initiated_by': 'System',
                            'download_url': url_for('download_server_backup_file', server_name=server_name, filename=backup_file.name),
                            'file_exists': True
                        })
    
    # Sort backups by creation date (newest first)
    system_backups.sort(key=lambda x: x['created'], reverse=True)
    server_backups.sort(key=lambda x: x['created'], reverse=True)
    
    return render_template('admin/backup_management.html', 
                         system_backups=system_backups, 
                         server_backups=server_backups)

@app.route('/download/backup/<filename>')
@login_required
def download_backup_file(filename):
    """Download a specific system backup file"""
    if not current_user.is_admin and not current_user.is_technical_agent:
        flash('Access denied. Admin or Technical privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Security check - only allow downloading .sql backup files
    if not filename.endswith('.sql') or '..' in filename:
        flash('Invalid backup file requested', 'danger')
        return redirect(url_for('list_all_backups'))
    
    backup_path = Path("static/backups") / filename
    if not backup_path.exists():
        flash('Backup file not found', 'danger')
        return redirect(url_for('list_all_backups'))
    
    try:
        return send_from_directory('static/backups', filename, as_attachment=True)
    except Exception as e:
        flash(f'Error downloading backup: {str(e)}', 'danger')
        return redirect(url_for('list_all_backups'))

@app.route('/download-backup/<int:backup_id>')
@login_required
def download_backup_by_id(backup_id):
    """Download a backup file by database record ID (legacy route)"""
    if not current_user.is_admin and not current_user.is_technical_agent:
        flash('Access denied. Admin or Technical privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Find the backup record in the database
    backup = DatabaseBackup.query.get_or_404(backup_id)
    
    if not backup.backup_path:
        flash('Backup file path not available', 'danger')
        return redirect(url_for('list_all_backups'))
    
    backup_path = Path(backup.backup_path)
    if not backup_path.exists():
        flash('Backup file not found on disk', 'danger')
        return redirect(url_for('list_all_backups'))
    
    try:
        # Determine the directory and filename for send_from_directory
        if 'servers/' in str(backup_path):
            # Server backup file
            parts = backup_path.parts
            servers_index = parts.index('servers')
            server_name = parts[servers_index + 1]
            filename = backup_path.name
            return send_from_directory(f'static/backups/servers/{server_name}', filename, as_attachment=True)
        else:
            # System backup file
            return send_from_directory('static/backups', backup_path.name, as_attachment=True)
    except Exception as e:
        flash(f'Error downloading backup: {str(e)}', 'danger')
        return redirect(url_for('list_all_backups'))

@app.route('/download/server-backup/<server_name>/<filename>')
@login_required
def download_server_backup_file(server_name, filename):
    """Download a specific server backup file"""
    if not current_user.is_admin and not current_user.is_technical_agent:
        flash('Access denied. Admin or Technical privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Security check - only allow downloading .bak backup files and prevent path traversal
    if not filename.endswith('.bak') or '..' in filename or '..' in server_name:
        flash('Invalid backup file requested', 'danger')
        return redirect(url_for('list_all_backups'))
    
    backup_path = Path("static/backups/servers") / server_name / filename
    if not backup_path.exists():
        flash('Server backup file not found', 'danger')
        return redirect(url_for('list_all_backups'))
    
    try:
        return send_from_directory(f'static/backups/servers/{server_name}', filename, as_attachment=True)
    except Exception as e:
        flash(f'Error downloading backup: {str(e)}', 'danger')
        return redirect(url_for('list_all_backups'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            # Check if user is approved before allowing login
            if not user.is_approved:
                flash('Your account is pending admin approval. Please contact the administrator.', 'warning')
                return render_template('login.html', form=form)
            
            login_user(user)
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('index')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page)
        flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User()
        user.username = form.username.data
        user.email = form.email.data
        user.set_password(form.password.data)
        user.is_approved = False  # New users require admin approval
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Your account is pending admin approval. Please contact the administrator to activate your account.', 'info')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Removed dashboard route - now using / as main dashboard

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Get filter parameters
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')
    search = request.args.get('search', '')
    
    # Build query
    query = ServerRequest.query
    
    if status_filter:
        query = query.filter(ServerRequest.status == status_filter)
    if priority_filter:
        query = query.filter(ServerRequest.priority == priority_filter)
    if search:
        query = query.filter(
            db.or_(
                ServerRequest.client_name.contains(search),
                ServerRequest.server_name.contains(search),
                ServerRequest.request_id.contains(search)
            )
        )
    
    requests = query.order_by(ServerRequest.created_at.desc()).all()
    
    # Statistics
    all_requests = ServerRequest.query.all()
    stats = {
        'total_requests': len(all_requests),
        'pending': len([r for r in all_requests if r.status == 'pending']),
        'approved': len([r for r in all_requests if r.status == 'approved']),
        'deployed': len([r for r in all_requests if r.status == 'deployed']),
        'rejected': len([r for r in all_requests if r.status == 'rejected'])
    }
    
    # Check if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'requests': [{
                'id': r.id,
                'request_id': r.request_id,
                'client_name': r.client_name,
                'server_name': r.server_name,
                'status': r.status,
                'priority': r.priority,
                'subdomain': r.subdomain,
                'project_name': r.project.name if r.project else 'Unknown',
                'created_at': r.created_at.strftime('%Y-%m-%d %H:%M') if r.created_at else 'Unknown'
            } for r in requests],
            'stats': stats,
            'total_shown': len(requests)
        })
    
    return render_template('admin_dashboard.html', requests=requests, stats=stats, 
                         status_filter=status_filter, priority_filter=priority_filter, search=search)

@app.route('/technical-dashboard')
@login_required
def technical_dashboard():
    if not current_user.has_permission('manage_servers'):
        flash('Access denied. Technical Agent privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Only admins see all servers - technical agents (including managers) use project-based filtering
    if current_user.is_admin:
        # Only admins see all servers
        servers = HetznerServer.query.all()
        # Get all system updates, backups, and deployments
        recent_updates = SystemUpdate.query.order_by(SystemUpdate.started_at.desc()).limit(10).all()
        recent_backups = DatabaseBackup.query.order_by(DatabaseBackup.started_at.desc()).limit(10).all()
        recent_deployments = DeploymentExecution.query.order_by(DeploymentExecution.started_at.desc()).limit(10).all()
    else:
        # All technical agents (including managers) see only servers from projects they have access to
        servers = current_user.get_accessible_servers()
        accessible_server_ids = [server.id for server in servers]
        
        # Filter activities to only show data from servers in accessible projects
        recent_updates = SystemUpdate.query.filter(SystemUpdate.server_id.in_(accessible_server_ids)).order_by(SystemUpdate.started_at.desc()).limit(10).all() if accessible_server_ids else []
        recent_backups = DatabaseBackup.query.filter(DatabaseBackup.server_id.in_(accessible_server_ids)).order_by(DatabaseBackup.started_at.desc()).limit(10).all() if accessible_server_ids else []
        recent_deployments = DeploymentExecution.query.filter(DeploymentExecution.server_id.in_(accessible_server_ids)).order_by(DeploymentExecution.started_at.desc()).limit(10).all() if accessible_server_ids else []
    
    # Statistics for technical dashboard
    stats = {
        'total_servers': len(servers),
        'running_servers': len([s for s in servers if s.status == 'running']),
        'stopped_servers': len([s for s in servers if s.status == 'stopped']),
        'failed_backups': len([b for b in recent_backups if b.status == 'failed']),
        'pending_updates': len([u for u in recent_updates if u.status in ['scheduled', 'running']]),
        'recent_deployments': len(recent_deployments)
    }
    
    return render_template('technical_dashboard.html', 
                         servers=servers, 
                         recent_updates=recent_updates,
                         recent_backups=recent_backups,
                         recent_deployments=recent_deployments,
                         stats=stats)

@app.route('/sales-dashboard')
@login_required  
def sales_dashboard():
    if not current_user.has_permission('create_requests'):
        flash('Access denied. Sales Agent privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Get user's requests (sales agents see their own requests)
    requests = ServerRequest.query.filter_by(user_id=current_user.id).order_by(ServerRequest.created_at.desc()).all()
    
    # Get client subscriptions managed by this sales agent
    subscriptions = ClientSubscription.query.filter_by(managed_by=current_user.id).order_by(ClientSubscription.subscription_end.asc()).all()
    
    # Get approved servers that clients can see
    approved_servers = HetznerServer.query.filter(HetznerServer.deployment_status == 'deployed').all()
    
    # Get unread notifications
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).limit(5).all()
    
    # Statistics for sales dashboard
    stats = {
        'total_requests': len(requests),
        'pending_requests': len([r for r in requests if r.status == 'pending']),
        'approved_requests': len([r for r in requests if r.status in ['approved', 'deploying', 'deployed']]),
        'rejected_requests': len([r for r in requests if r.status == 'rejected']),
        'total_subscriptions': len(subscriptions),
        'expiring_soon': len([s for s in subscriptions if s.is_expiring_soon and s.is_active]),
        'active_subscriptions': len([s for s in subscriptions if s.is_active]),
        'total_revenue': sum([s.monthly_cost for s in subscriptions if s.is_active])
    }
    
    return render_template('sales_dashboard.html', 
                         requests=requests, 
                         subscriptions=subscriptions,
                         approved_servers=approved_servers,
                         notifications=notifications, 
                         stats=stats)

@app.route('/request-server', methods=['GET', 'POST'])
@login_required
def request_server():
    # Only sales agents and admins can create requests
    if not current_user.has_permission('create_requests'):
        flash('Access denied. You do not have permission to create server requests.', 'danger')
        return redirect(url_for('index'))
        
    form = ServerRequestForm()
    
    # Populate project choices based on user's access
    # For sales agents and admins creating requests, show only active projects 
    # (sales agents need to create requests for any project)
    if current_user.is_admin:
        projects = HetznerProject.query.filter_by(is_active=True).all()
        form.project_id.choices = [(p.id, f"{p.name} - {p.base_domain if p.base_domain else 'No domain'}") for p in projects]
    elif current_user.is_sales_agent:
        # Sales agents can create requests for only active projects
        projects = HetznerProject.query.filter_by(is_active=True).all()
        form.project_id.choices = [(p.id, f"{p.name} - {p.base_domain if p.base_domain else 'No domain'}") for p in projects]
    else:
        # Technical agents only see their active assigned projects
        accessible_projects = [p for p in current_user.get_accessible_projects() if p.is_active]
        form.project_id.choices = [(p.id, f"{p.name} - {p.base_domain if p.base_domain else 'No domain'}") for p in accessible_projects]
    
    # Debug logging
    app.logger.info(f"User: {current_user.username}, Role: {current_user.role}, IsAdmin: {current_user.is_admin}")
    app.logger.info(f"Available projects count: {len(form.project_id.choices)}")
    app.logger.info(f"Project choices: {form.project_id.choices}")
    
    # Add empty choice at the beginning for proper form validation
    if form.project_id.choices:
        form.project_id.choices.insert(0, (0, 'Select a project...'))
    else:
        form.project_id.choices = [(0, 'No projects available')]
    
    if form.validate_on_submit():
        # Auto-generate server name from client name
        server_name = ServerRequest.generate_server_name(form.client_name.data)
        
        # Auto-assign hardware specs based on estimated usage
        hardware_specs = ServerRequest.assign_hardware_specs(form.estimated_usage.data)
        
        server_request = ServerRequest()
        server_request.user_id = current_user.id
        server_request.client_name = form.client_name.data
        server_request.server_name = server_name
        server_request.subdomain = form.subdomain.data
        server_request.project_id = form.project_id.data
        server_request.server_type = hardware_specs['server_type']
        server_request.cpu_cores = hardware_specs['cpu_cores']
        server_request.memory_gb = hardware_specs['memory_gb']
        server_request.storage_gb = hardware_specs['storage_gb']
        server_request.operating_system = 'ubuntu-22.04'  # Default OS
        server_request.business_justification = form.business_justification.data
        server_request.estimated_usage = form.estimated_usage.data
        server_request.priority = form.priority.data
        
        db.session.add(server_request)
        db.session.commit()
        
        # Create notification for user
        notification = Notification()
        notification.user_id = current_user.id
        notification.title = 'Server Request Submitted'
        notification.message = f'Your server request for "{form.client_name.data}" (server: {server_name}) has been submitted and is pending approval.'
        notification.type = 'info'
        notification.request_id = server_request.id
        db.session.add(notification)
        db.session.commit()
        
        flash(f'Server request submitted successfully! Request ID: {server_request.request_id}', 'success')
        return redirect(url_for('index'))
    
    return render_template('request_server.html', form=form)

@app.route('/request/<request_id>')
@login_required
def request_detail(request_id):
    server_request = ServerRequest.query.filter_by(request_id=request_id).first_or_404()
    
    # Check if user can view this request
    if not current_user.is_admin and server_request.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    form = AdminReviewForm() if current_user.is_admin else None
    
    return render_template('request_detail.html', request=server_request, form=form)

@app.route('/request/<request_id>/review', methods=['POST'])
@login_required
def review_request(request_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    server_request = ServerRequest.query.filter_by(request_id=request_id).first_or_404()
    form = AdminReviewForm()
    
    if form.validate_on_submit():
        server_request.status = form.status.data
        server_request.admin_notes = form.admin_notes.data
        server_request.reviewed_by = current_user.id
        server_request.reviewed_at = datetime.utcnow()
        
        # Create notification for user
        status_message = 'approved' if form.status.data == 'approved' else 'rejected'
        notification = Notification()
        notification.user_id = server_request.user_id
        notification.title = f'Server Request {status_message.title()}'
        notification.message = f'Your server request "{server_request.server_name}" has been {status_message}.'
        notification.type = 'success' if form.status.data == 'approved' else 'warning'
        notification.request_id = server_request.id
        db.session.add(notification)
        db.session.commit()
        
        flash(f'Request {status_message} successfully!', 'success')
        
        # If approved, automatically provision server and create DNS record
        if form.status.data == 'approved':
            # Start background server provisioning
            try:
                result = provision_server_and_dns(server_request)
                if result['success']:
                    flash('Server provisioning started successfully! The server will be created and DNS configured automatically.', 'success')
                else:
                    flash(f'Error starting server provisioning: {result["error"]}', 'warning')
            except Exception as e:
                app.logger.error(f"Error in server provisioning: {e}")
                flash('Server provisioning could not be started. Please check the logs.', 'warning')
    
    return redirect(url_for('request_detail', request_id=request_id))

@app.route('/request/<request_id>/deploy')
@login_required
def deploy_server(request_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    server_request = ServerRequest.query.filter_by(request_id=request_id).first_or_404()
    
    if server_request.status != 'approved':
        flash('Request must be approved before deployment.', 'warning')
        return redirect(url_for('request_detail', request_id=request_id))
    
    # Start deployment process
    server_request.status = 'deploying'
    server_request.deployment_progress = 0
    # Generate mock IP address
    server_request.server_ip = f"10.0.{random.randint(1, 254)}.{random.randint(1, 254)}"
    db.session.commit()
    
    return render_template('deploy_progress.html', request=server_request)

@app.route('/api/deployment-progress/<request_id>')
@login_required
def deployment_progress(request_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    server_request = ServerRequest.query.filter_by(request_id=request_id).first_or_404()
    
    if server_request.status == 'deploying':
        # Simulate deployment progress
        current_progress = server_request.deployment_progress
        if current_progress < 100:
            # Increment progress randomly
            increment = random.randint(5, 25)
            new_progress = min(current_progress + increment, 100)
            server_request.deployment_progress = new_progress
            
            if new_progress == 100:
                server_request.status = 'deployed'
                server_request.deployed_at = datetime.utcnow()
                server_request.deployment_notes = f"Successfully deployed {server_request.application_name} on {server_request.server_name}"
                
                # Create success notification
                notification = Notification()
                notification.user_id = server_request.user_id
                notification.title = 'Server Deployed Successfully'
                notification.message = f'Your server "{server_request.server_name}" has been deployed successfully at IP {server_request.server_ip}.'
                notification.type = 'success'
                notification.request_id = server_request.id
                db.session.add(notification)
            
            db.session.commit()
    
    return jsonify({
        'progress': server_request.deployment_progress,
        'status': server_request.status,
        'server_ip': server_request.server_ip
    })

@app.route('/notifications/mark-read/<int:notification_id>')
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id == current_user.id:
        notification.is_read = True
        db.session.commit()
    return redirect(request.referrer or url_for('index'))

@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user)
    
    if form.validate_on_submit():
        from werkzeug.security import generate_password_hash
        
        # Update user details
        current_user.username = form.username.data
        current_user.email = form.email.data
        
        # Update password if provided
        if form.new_password.data:
            current_user.password_hash = generate_password_hash(form.new_password.data)
        
        db.session.commit()
        flash('Your profile has been updated successfully!', 'success')
        return redirect(url_for('index'))
    
    # Pre-populate form with current user data
    if request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    
    return render_template('edit_profile.html', form=form)

# Server Management Routes

@app.route('/servers')
@login_required
def servers_list():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Get filter parameters
    status_filter = request.args.get('status', '')
    project_filter = request.args.get('project', '')
    search = request.args.get('search', '')
    
    # Build query
    query = HetznerServer.query
    
    if status_filter:
        query = query.filter(HetznerServer.status == status_filter)
    if project_filter:
        query = query.filter(HetznerServer.project_id == project_filter)
    if search:
        query = query.filter(
            db.or_(
                HetznerServer.name.contains(search),
                HetznerServer.reverse_dns.contains(search),
                HetznerServer.public_ip.contains(search)
            )
        )
    
    servers = query.order_by(HetznerServer.last_synced.desc()).all()
    
    # Get server statistics (from all servers for stats)
    all_servers = HetznerServer.query.all()
    stats = {
        'total_servers': len(all_servers),
        'running': len([s for s in all_servers if s.status == 'running']),
        'stopped': len([s for s in all_servers if s.status == 'stopped']),
        'deploying': len([s for s in all_servers if s.deployment_status == 'deploying'])
    }
    
    # Get projects for filter dropdown
    projects = HetznerProject.query.all()
    
    # Check if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'servers': [{
                'id': s.id,
                'name': s.name,
                'status': s.status,
                'server_type': s.server_type,
                'public_ip': s.public_ip,
                'reverse_dns': s.reverse_dns,
                'location': s.location,
                'project_name': s.project.name if s.project else 'Unknown',
                'last_synced': s.last_synced.strftime('%Y-%m-%d %H:%M') if s.last_synced else 'Never'
            } for s in servers],
            'stats': stats,
            'total_shown': len(servers)
        })
    
    return render_template('servers_list.html', servers=servers, stats=stats,
                         status_filter=status_filter, project_filter=project_filter, 
                         search=search, projects=projects)

@app.route('/servers/sync')
@login_required
def sync_servers():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    try:
        hetzner_service = HetznerService()
        result = hetzner_service.sync_servers_from_hetzner()
        
        if result['success']:
            flash(f'Servers synced successfully! {result["synced"]} new, {result["updated"]} updated from {result["total"]} total.', 'success')
        else:
            flash(f'Error syncing servers: {result["error"]}', 'danger')
    except Exception as e:
        flash(f'Error connecting to Hetzner: {str(e)}', 'danger')
    
    return redirect(url_for('servers_list'))

@app.route('/servers/<int:server_id>')
@login_required
def server_detail(server_id):
    # Allow technical agents access to servers in their projects
    if not (current_user.is_admin or current_user.is_technical_agent):
        flash('Access denied. Technical Agent or Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    server = HetznerServer.query.get_or_404(server_id)
    
    # Check if technical agent has access to this server's project
    if not current_user.is_admin:
        accessible_servers = current_user.get_accessible_servers()
        accessible_server_ids = [s.id for s in accessible_servers]
        if server_id not in accessible_server_ids:
            flash('Access denied. You do not have permission to view this server.', 'danger')
            return redirect(url_for('server_operations'))
    
    # Get deployment scripts for execution form
    scripts = DeploymentScript.query.all()
    
    # Get recent deployments
    recent_deployments = DeploymentExecution.query.filter_by(server_id=server_id).order_by(DeploymentExecution.started_at.desc()).limit(10).all()
    
    # Create forms
    management_form = ServerManagementForm()
    execution_form = ExecuteDeploymentForm()
    execution_form.script_id.choices = [(s.id, s.name) for s in scripts]
    
    return render_template('server_detail.html', 
                         server=server, 
                         management_form=management_form,
                         execution_form=execution_form,
                         recent_deployments=recent_deployments)

@app.route('/servers/<int:server_id>/manage', methods=['POST'])
@login_required
def manage_server(server_id):
    # Allow technical agents access to servers in their projects
    if not (current_user.is_admin or current_user.is_technical_agent):
        flash('Access denied. Technical Agent or Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    server = HetznerServer.query.get_or_404(server_id)
    
    # Check if technical agent has access to this server's project
    if not current_user.is_admin:
        accessible_servers = current_user.get_accessible_servers()
        accessible_server_ids = [s.id for s in accessible_servers]
        if server_id not in accessible_server_ids:
            flash('Access denied. You do not have permission to manage this server.', 'danger')
            return redirect(url_for('server_operations'))
    form = ServerManagementForm()
    
    if form.validate_on_submit():
        # Check if server is client-managed (we don't manage infrastructure)
        if server.is_self_hosted:
            flash('Infrastructure operations (start/stop/reboot) are not available for client-managed servers. We only manage project deployments on these servers.', 'warning')
            return redirect(url_for('server_detail', server_id=server_id))
        
        try:
            hetzner_service = HetznerService(project_id=server.project_id)
            
            if form.action.data == 'start':
                result = hetzner_service.start_server(server.hetzner_id)
            elif form.action.data == 'stop':
                result = hetzner_service.stop_server(server.hetzner_id)
            elif form.action.data == 'reboot':
                result = hetzner_service.reboot_server(server.hetzner_id)
            else:
                flash('Invalid action', 'danger')
                return redirect(url_for('server_detail', server_id=server_id))
            
            if result['success']:
                flash(f'Server {form.action.data} action initiated successfully!', 'success')
                # Update server status immediately to final expected status
                # Map intermediate states to final states since Hetzner transitions quickly
                if form.action.data == 'start':
                    server.status = 'running'  # starting -> running
                elif form.action.data == 'stop':
                    server.status = 'stopped'  # stopping -> stopped  
                elif form.action.data == 'reboot':
                    server.status = 'running'  # rebooting -> running
                
                server.last_synced = datetime.utcnow()
                db.session.commit()
                app.logger.info(f"Server {server.name} status updated to: {server.status}")
                    
            else:
                flash(f'Error executing {form.action.data}: {result["error"]}', 'danger')
                
        except Exception as e:
            flash(f'Error managing server: {str(e)}', 'danger')
    
    return redirect(url_for('server_detail', server_id=server_id))

@app.route('/servers/add-self-hosted', methods=['GET', 'POST'])
@login_required
def add_self_hosted_server():
    # Only admins and technical managers can add self-hosted servers
    if not (current_user.is_admin or (current_user.is_technical_agent and current_user.is_manager)):
        flash('Access denied. Administrator or Technical Manager privileges required.', 'danger')
        return redirect(url_for('index'))
    
    form = SelfHostedServerForm()
    
    # Populate project choices based on user access
    if current_user.is_admin:
        projects = HetznerProject.query.filter(HetznerProject.is_active == True).all()
    else:
        projects = current_user.get_accessible_projects()
    
    form.project_id.choices = [(0, 'Select Project')] + [(p.id, p.name) for p in projects]
    
    if form.validate_on_submit():
        try:
            # Create new self-hosted server
            server = HetznerServer(
                server_source='self_hosted',
                hetzner_id=None,  # No Hetzner ID for self-hosted servers
                name=form.name.data,
                status='running',  # Assume running for self-hosted servers
                server_type='Client-Managed',  # Default type for client-managed servers
                image=None,  # Not needed for client-managed servers
                client_name=form.client_name.data,
                client_contact=form.client_contact.data,
                project_id=form.project_id.data if form.project_id.data != 0 else None,
                public_ip=form.public_ip.data,
                private_ip=form.private_ip.data,
                reverse_dns=form.reverse_dns.data,
                datacenter=None,  # Not needed for client-managed servers
                location=None,  # Not needed for client-managed servers
                cpu_cores=None,  # Not needed for client-managed servers
                memory_gb=None,  # Not needed for client-managed servers
                disk_gb=None,  # Not needed for client-managed servers
                managed_by=current_user.id,
                created_at=datetime.utcnow(),
                last_synced=datetime.utcnow()
            )
            
            db.session.add(server)
            db.session.commit()
            
            flash(f'Self-hosted server "{server.name}" added successfully!', 'success')
            return redirect(url_for('server_operations'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding self-hosted server: {str(e)}', 'danger')
    
    return render_template('add_self_hosted_server.html', form=form)

@app.route('/servers/<int:server_id>/deploy', methods=['POST'])
@login_required
def deploy_to_server(server_id):
    # Allow technical agents access to servers in their projects
    if not (current_user.is_admin or current_user.is_technical_agent):
        flash('Access denied. Technical Agent or Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    server = HetznerServer.query.get_or_404(server_id)
    
    # Check if technical agent has access to this server's project
    if not current_user.is_admin:
        accessible_servers = current_user.get_accessible_servers()
        accessible_server_ids = [s.id for s in accessible_servers]
        if server_id not in accessible_server_ids:
            flash('Access denied. You do not have permission to deploy to this server.', 'danger')
            return redirect(url_for('server_operations'))
    form = ExecuteDeploymentForm()
    
    # Set choices for the form
    scripts = DeploymentScript.query.all()
    form.script_id.choices = [(s.id, s.name) for s in scripts]
    
    if form.validate_on_submit():
        try:
            # Parse execution variables
            execution_vars = {}
            if form.execution_variables.data:
                import json
                execution_vars = json.loads(form.execution_variables.data)
            
            ansible_service = AnsibleService()
            result = ansible_service.execute_deployment(
                server_id=server_id,
                script_id=form.script_id.data,
                user_id=current_user.id,
                variables=execution_vars
            )
            
            if result['success']:
                flash(f'Deployment started successfully! Execution ID: {result["execution_id"]}', 'success')
                return redirect(url_for('deployment_execution', execution_id=result["execution_id"]))
            else:
                flash(f'Error starting deployment: {result["error"]}', 'danger')
                
        except json.JSONDecodeError:
            flash('Invalid JSON in execution variables', 'danger')
        except Exception as e:
            flash(f'Error executing deployment: {str(e)}', 'danger')
    
    return redirect(url_for('server_detail', server_id=server_id))

# Deployment Scripts Management

@app.route('/deployment-scripts')
@login_required
def deployment_scripts():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    scripts = DeploymentScript.query.order_by(DeploymentScript.created_at.desc()).all()
    return render_template('deployment_scripts.html', scripts=scripts)

@app.route('/deployment-scripts/new', methods=['GET', 'POST'])
@login_required
def new_deployment_script():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    form = DeploymentScriptForm()
    
    if form.validate_on_submit():
        try:
            # Validate Ansible playbook
            ansible_service = AnsibleService()
            validation = ansible_service.validate_playbook(form.ansible_playbook.data)
            
            if not validation['valid']:
                flash(f'Invalid Ansible playbook: {validation["error"]}', 'danger')
                return render_template('deployment_script_form.html', form=form, title='New Deployment Script')
            
            # Validate variables JSON if provided
            if form.variables.data:
                import json
                json.loads(form.variables.data)
            
            script = DeploymentScript()
            script.name = form.name.data
            script.description = form.description.data
            script.ansible_playbook = form.ansible_playbook.data
            script.variables = form.variables.data
            script.created_by = current_user.id
            
            db.session.add(script)
            db.session.commit()
            
            flash('Deployment script created successfully!', 'success')
            return redirect(url_for('deployment_scripts'))
            
        except json.JSONDecodeError:
            flash('Invalid JSON in variables field', 'danger')
        except Exception as e:
            flash(f'Error creating script: {str(e)}', 'danger')
    
    return render_template('deployment_script_form.html', form=form, title='New Deployment Script')

@app.route('/deployment-scripts/<int:script_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_deployment_script(script_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    script = DeploymentScript.query.get_or_404(script_id)
    form = DeploymentScriptForm(obj=script)
    
    if form.validate_on_submit():
        try:
            # Validate Ansible playbook
            ansible_service = AnsibleService()
            validation = ansible_service.validate_playbook(form.ansible_playbook.data)
            
            if not validation['valid']:
                flash(f'Invalid Ansible playbook: {validation["error"]}', 'danger')
                return render_template('deployment_script_form.html', form=form, title='Edit Deployment Script', script=script)
            
            # Validate variables JSON if provided
            if form.variables.data:
                import json
                json.loads(form.variables.data)
            
            script.name = form.name.data
            script.description = form.description.data
            script.ansible_playbook = form.ansible_playbook.data
            script.variables = form.variables.data
            script.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash('Deployment script updated successfully!', 'success')
            return redirect(url_for('deployment_scripts'))
            
        except json.JSONDecodeError:
            flash('Invalid JSON in variables field', 'danger')
        except Exception as e:
            flash(f'Error updating script: {str(e)}', 'danger')
    
    return render_template('deployment_script_form.html', form=form, title='Edit Deployment Script', script=script)

@app.route('/deployment-scripts/samples')
@login_required
def sample_deployment_scripts():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    ansible_service = AnsibleService()
    samples = ansible_service.get_sample_playbooks()
    
    return render_template('sample_scripts.html', samples=samples)

@app.route('/deployment-scripts/samples/<sample_name>/create', methods=['POST'])
@login_required
def create_from_sample(sample_name):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    try:
        ansible_service = AnsibleService()
        samples = ansible_service.get_sample_playbooks()
        
        if sample_name not in samples:
            flash('Sample script not found', 'danger')
            return redirect(url_for('sample_deployment_scripts'))
        
        sample = samples[sample_name]
        
        script = DeploymentScript()
        script.name = sample['name']
        script.description = sample['description']
        script.ansible_playbook = sample['playbook']
        script.variables = json.dumps(sample['variables'], indent=2)
        script.created_by = current_user.id
        
        db.session.add(script)
        db.session.commit()
        
        flash(f'Sample script "{sample["name"]}" created successfully!', 'success')
        return redirect(url_for('deployment_scripts'))
        
    except Exception as e:
        flash(f'Error creating sample script: {str(e)}', 'danger')
        return redirect(url_for('sample_deployment_scripts'))

# Deployment Execution Tracking

@app.route('/deployments')
@login_required
def deployment_executions():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    executions = DeploymentExecution.query.order_by(DeploymentExecution.started_at.desc()).all()
    return render_template('deployment_executions.html', executions=executions)

@app.route('/deployments/<execution_id>')
@login_required
def deployment_execution(execution_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    execution = DeploymentExecution.query.filter_by(execution_id=execution_id).first_or_404()
    return render_template('deployment_execution_detail.html', execution=execution)

@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# Subscription Management Routes (Sales Agents)
@app.route('/subscriptions')
@login_required
def subscriptions():
    if not current_user.has_permission('manage_subscriptions'):
        flash('Access denied. Sales Agent privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Sales agents see only their managed subscriptions
    if current_user.is_sales_agent:
        subscriptions = ClientSubscription.query.filter_by(managed_by=current_user.id).all()
    else:  # Admins see all subscriptions
        subscriptions = ClientSubscription.query.all()
    
    return render_template('subscriptions.html', subscriptions=subscriptions)

@app.route('/subscription/<int:subscription_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_subscription(subscription_id):
    subscription = ClientSubscription.query.get_or_404(subscription_id)
    
    # Check permissions
    if not current_user.has_permission('manage_subscriptions'):
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    # Sales agents can only edit their own managed subscriptions
    if current_user.is_sales_agent and subscription.managed_by != current_user.id:
        flash('Access denied. You can only edit subscriptions you manage.', 'danger')
        return redirect(url_for('subscriptions'))
    
    if request.method == 'POST':
        subscription.subscription_start = datetime.strptime(request.form['subscription_start'], '%Y-%m-%d').date()
        subscription.subscription_end = datetime.strptime(request.form['subscription_end'], '%Y-%m-%d').date()
        subscription.subscription_type = request.form['subscription_type']
        subscription.monthly_cost = float(request.form['monthly_cost'])
        subscription.auto_renewal = 'auto_renewal' in request.form
        subscription.is_active = 'is_active' in request.form
        
        db.session.commit()
        flash('Subscription updated successfully!', 'success')
        return redirect(url_for('subscriptions'))
    
    return render_template('edit_subscription.html', subscription=subscription)

# Server Operations Routes (Technical Agents)
@app.route('/server-operations')
@login_required
def server_operations():
    if not current_user.has_permission('server_operations'):
        flash('Access denied. Technical Agent privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Get filter parameters
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    project_filter = request.args.get('project', '')
    server_source_filter = request.args.get('server_source', '')
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Only admins have complete system access - see all servers
    if current_user.is_admin:
        query = HetznerServer.query.filter(HetznerServer.status.in_(['running', 'stopped']))
    else:
        # All technical agents (including managers) see only servers from projects they have access to
        accessible_servers = current_user.get_accessible_servers()
        accessible_server_ids = [s.id for s in accessible_servers if s.status in ['running', 'stopped']]
        query = HetznerServer.query.filter(HetznerServer.id.in_(accessible_server_ids)) if accessible_server_ids else HetznerServer.query.filter(False)
    
    # Apply filters
    if search:
        query = query.filter(
            db.or_(
                HetznerServer.name.ilike(f'%{search}%'),
                HetznerServer.public_ip.ilike(f'%{search}%'),
                HetznerServer.reverse_dns.ilike(f'%{search}%')
            )
        )
    
    if status_filter:
        query = query.filter(HetznerServer.status == status_filter)
    
    if project_filter:
        query = query.filter(HetznerServer.project_id == project_filter)
    
    if server_source_filter:
        query = query.filter(HetznerServer.server_source == server_source_filter)
    
    servers = query.all()
    
    # Get available projects for filter dropdown
    if current_user.is_admin:
        projects = HetznerProject.query.filter(HetznerProject.is_active == True).all()
    else:
        projects = current_user.get_accessible_projects()
    
    if is_ajax:
        servers_data = []
        for server in servers:
            last_backup = None
            if server.backups:
                completed_backups = [b for b in server.backups if b.completed_at]
                if completed_backups:
                    last_backup = max(completed_backups, key=lambda x: x.completed_at)
            
            last_update = None
            if server.system_updates:
                completed_updates = [u for u in server.system_updates if u.completed_at]
                if completed_updates:
                    last_update = max(completed_updates, key=lambda x: x.completed_at)
            
            servers_data.append({
                'id': server.id,
                'name': server.name,
                'server_type': server.server_type,
                'public_ip': server.public_ip or 'No IP',
                'reverse_dns': server.reverse_dns,
                'project_name': server.project.name if server.project else 'No Project',
                'last_backup': convert_to_cairo_timezone(last_backup.completed_at).strftime('%Y-%m-%d %H:%M') if last_backup and last_backup.completed_at else 'Never',
                'last_backup_status': last_backup.status if last_backup else None,
                'last_update': convert_to_cairo_timezone(last_update.completed_at).strftime('%Y-%m-%d %H:%M') if last_update and last_update.completed_at else 'Never',
                'last_update_status': last_update.status if last_update else None,
                'status': server.status
            })
        
        return jsonify({
            'success': True,
            'servers': servers_data,
            'total_shown': len(servers_data)
        })
    
    
    return render_template('server_operations.html', 
                         servers=servers, 
                         projects=projects,
                         search=search,
                         status_filter=status_filter,
                         project_filter=project_filter,
                         server_source_filter=server_source_filter)

@app.route('/server/<int:server_id>/backup', methods=['POST'])
@login_required
def create_backup(server_id):
    # Check if it's an AJAX request early for error handling
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if not current_user.has_permission('database_operations'):
        if is_ajax:
            return jsonify({'success': False, 'message': 'Access denied. Technical Agent privileges required.'}), 403
        flash('Access denied. Technical Agent privileges required.', 'danger')
        return redirect(url_for('index'))
    
    server = HetznerServer.query.get_or_404(server_id)
    
    # Check if user has access to this specific server
    if not current_user.has_server_access(server_id, 'write'):
        if is_ajax:
            return jsonify({'success': False, 'message': 'Access denied. You do not have access to this server.'}), 403
        flash('Access denied. You do not have access to this server.', 'danger')
        return redirect(url_for('server_operations'))
    
    # Create backup record
    backup = DatabaseBackup()
    backup.server_id = server_id
    backup.database_name = request.form.get('database_name', 'main')
    backup.backup_type = request.form.get('backup_type', 'full')
    backup.started_at = datetime.utcnow()
    backup.initiated_by = current_user.id
    
    db.session.add(backup)
    db.session.commit()
    
    try:
        # Check if project has SSH configuration
        if not server.project or not server.project.ssh_private_key:
            backup.status = 'failed'
            backup.error_log = 'No SSH private key configured for this project. Please configure SSH access in project settings.'
            backup.completed_at = datetime.utcnow()
            db.session.commit()
            error_msg = f'Project {server.project.name if server.project else "Unknown"} requires SSH key configuration for remote backup execution'
            if is_ajax:
                return jsonify({'success': False, 'message': error_msg, 'status': 'failed'})
            flash(error_msg, 'warning')
            return redirect(url_for('server_operations'))
        
        # Use SSH service to execute backup command remotely and prepare file for download
        ssh_service = SSHService()
        
        # Create backup directory structure organized by server name
        server_backup_dir = Path(f"static/backups/servers/{server.name}")
        server_backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate backup filename (will be updated with actual filename from server)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{backup.database_name}_{timestamp}.bak"
        local_backup_path = server_backup_dir / backup_filename
        
        # Execute the backup command - backup files are created in /home/dynamic/nova-hr-docker/mssql/backup/
        backup_command = f"cd /home/dynamic/nova-hr-docker && docker compose exec backup ./usr/src/app/backup-db.sh && echo 'BACKUP_COMPLETED' && ls -la /home/dynamic/nova-hr-docker/mssql/backup/ | tail -1"
        
        success, stdout_output, stderr_output = ssh_service.execute_command(
            server=server,
            command=backup_command,
            timeout=300  # 5 minute timeout
        )
        
        # Update record with results
        backup.completed_at = datetime.utcnow()
        backup.backup_log = stdout_output
        
        if success:
            # Step 2: Find and download the latest backup file from the server
            try:
                # Get the latest backup file from the remote server
                latest_backup = ssh_service.get_latest_backup_file(server)
                
                if latest_backup:
                    # Update local filename to match the actual backup filename
                    actual_filename = Path(latest_backup).name
                    local_backup_path = server_backup_dir / actual_filename
                    
                    # Download the backup file from remote server to our local storage
                    download_success = ssh_service.download_file(
                        server=server,
                        remote_path=latest_backup,
                        local_path=str(local_backup_path)
                    )
                    
                    if download_success and local_backup_path.exists():
                        # Get actual file size
                        file_size = local_backup_path.stat().st_size
                        backup.backup_path = str(local_backup_path)
                        backup.backup_size = file_size
                        backup.status = 'completed'
                        
                        flash(f'Database backup completed and downloaded for {server.name} ({file_size:,} bytes)', 'success')
                    else:
                        backup.status = 'failed'
                        backup.error_log = 'Backup created on server but failed to download to management system'
                        flash(f'Backup created on {server.name} but failed to download to management system', 'warning')
                else:
                    backup.status = 'failed'
                    backup.error_log = 'No backup file found after backup command execution'
                    flash(f'Backup command executed but no backup file found on {server.name}', 'warning')
                    
            except Exception as transfer_error:
                backup.status = 'failed'
                backup.error_log = f'File transfer error: {str(transfer_error)}'
                flash(f'Backup process failed during file transfer: {str(transfer_error)}', 'warning')
        else:
            backup.status = 'failed'
            backup.error_log = stderr_output
            flash(f'Database backup failed on {server.name}. Check logs for details.', 'danger')
        
        db.session.commit()
        
    except Exception as e:
        backup.status = 'failed'
        backup.error_log = str(e)
        backup.completed_at = datetime.utcnow()
        db.session.commit()
        flash(f'Error executing backup command: {str(e)}', 'danger')
    
    # Return appropriate response
    if is_ajax:
        return jsonify({
            'success': backup.status == 'completed',
            'message': f'Backup {"completed" if backup.status == "completed" else "failed"} for {server.name}',
            'timestamp': convert_to_cairo_timezone(backup.completed_at).strftime('%Y-%m-%d %H:%M') if backup.completed_at else None,
            'status': backup.status
        })
    
    return redirect(url_for('server_operations'))

@app.route('/server/<int:server_id>/update', methods=['POST'])
@login_required
def create_system_update(server_id):
    # Check if it's an AJAX request early for error handling
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if not current_user.has_permission('system_updates'):
        if is_ajax:
            return jsonify({'success': False, 'message': 'Access denied. Technical Agent privileges required.'}), 403
        flash('Access denied. Technical Agent privileges required.', 'danger')
        return redirect(url_for('index'))
    
    server = HetznerServer.query.get_or_404(server_id)
    
    # Check if user has access to this specific server
    if not current_user.has_server_access(server_id, 'write'):
        if is_ajax:
            return jsonify({'success': False, 'message': 'Access denied. You do not have access to this server.'}), 403
        flash('Access denied. You do not have access to this server.', 'danger')
        return redirect(url_for('server_operations'))
    
    # Create system update record
    update = SystemUpdate()
    update.server_id = server_id
    update.update_type = request.form.get('update_type', 'deployment')
    update.update_description = request.form.get('description', 'Nova HR Docker deployment script execution')
    update.started_at = datetime.utcnow()
    update.initiated_by = current_user.id
    
    db.session.add(update)
    db.session.commit()
    
    try:
        # Check if project has SSH configuration
        if not server.project or not server.project.ssh_private_key:
            update.status = 'failed'
            update.error_log = 'No SSH private key configured for this project. Please configure SSH access in project settings.'
            update.completed_at = datetime.utcnow()
            db.session.commit()
            error_msg = f'Project {server.project.name if server.project else "Unknown"} requires SSH key configuration for remote script execution'
            if is_ajax:
                return jsonify({'success': False, 'message': error_msg, 'status': 'failed'})
            flash(error_msg, 'warning')
            return redirect(url_for('server_operations'))
        
        # Use SSH service to execute deployment script remotely
        ssh_service = SSHService()
        
        # Execute the deployment script directly on the server
        deployment_command = get_default_deploy_script()
        
        # Execute the command via SSH
        success, stdout_output, stderr_output = ssh_service.execute_command(
            server=server,
            command=deployment_command,
            timeout=300  # 5 minute timeout
        )
        
        # Update record with results
        update.completed_at = datetime.utcnow()
        update.execution_log = stdout_output
        
        if success:
            update.status = 'completed'
            flash(f'Nova HR deployment script executed successfully on {server.name}', 'success')
        else:
            update.status = 'failed'
            update.error_log = stderr_output
            flash(f'Deployment script failed on {server.name}. Check logs for details.', 'danger')
        
        db.session.commit()
        
    except subprocess.TimeoutExpired:
        update.status = 'failed'
        update.error_log = 'Script execution timed out after 5 minutes'
        update.completed_at = datetime.utcnow()
        db.session.commit()
        flash(f'Deployment script timed out for {server.name}', 'danger')
        
    except Exception as e:
        update.status = 'failed'
        update.error_log = str(e)
        update.completed_at = datetime.utcnow()
        db.session.commit()
        flash(f'Error executing deployment script: {str(e)}', 'danger')
    
    # Return appropriate response
    if is_ajax:
        return jsonify({
            'success': update.status == 'completed',
            'message': f'Update {"completed" if update.status == "completed" else "failed"} for {server.name}',
            'timestamp': convert_to_cairo_timezone(update.completed_at).strftime('%Y-%m-%d %H:%M') if update.completed_at else None,
            'status': update.status
        })
    
    return redirect(url_for('server_operations'))

@app.route('/project/<int:project_id>/configure-ssh', methods=['GET', 'POST'])
@login_required
def configure_project_ssh(project_id):
    if not current_user.has_permission('server_operations'):
        flash('Access denied. Technical Agent privileges required.', 'danger')
        return redirect(url_for('index'))
    
    project = HetznerProject.query.get_or_404(project_id)
    
    if request.method == 'POST':
        # Update SSH configuration for the entire project
        project.ssh_username = request.form.get('ssh_username', 'root')
        project.ssh_port = int(request.form.get('ssh_port', 22))
        project.ssh_private_key = request.form.get('ssh_private_key')
        project.ssh_public_key = request.form.get('ssh_public_key')
        project.ssh_key_passphrase = request.form.get('ssh_key_passphrase')
        
        db.session.commit()
        flash(f'SSH configuration updated for project {project.name}', 'success')
        return redirect(url_for('configure_project_ssh', project_id=project_id))
    
    return render_template('configure_project_ssh.html', project=project)

@app.route('/project/<int:project_id>/test-ssh', methods=['POST'])
@login_required
def test_project_ssh_connection(project_id):
    if not current_user.has_permission('server_operations'):
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    project = HetznerProject.query.get_or_404(project_id)
    
    # Temporarily update project with test values
    original_values = {
        'ssh_username': project.ssh_username,
        'ssh_port': project.ssh_port,
        'ssh_private_key': project.ssh_private_key,
        'ssh_public_key': project.ssh_public_key,
        'ssh_key_passphrase': project.ssh_key_passphrase
    }
    
    # Use form values for testing
    project.ssh_username = request.form.get('ssh_username', 'root')
    project.ssh_port = int(request.form.get('ssh_port', 22))
    project.ssh_private_key = request.form.get('ssh_private_key')
    project.ssh_public_key = request.form.get('ssh_public_key')
    project.ssh_key_passphrase = request.form.get('ssh_key_passphrase')
    
    # Test with the first server in the project
    server = project.servers[0] if project.servers else None
    if not server:
        return jsonify({'success': False, 'error': 'No servers available in this project for testing'})
    
    try:
        ssh_service = SSHService()
        success, message = ssh_service.test_connection(server)
        
        if success:
            # Update test timestamp for project
            project.ssh_connection_tested = True
            project.ssh_last_test = datetime.utcnow()
            db.session.commit()
            return jsonify({'success': True, 'message': f'Connection successful to {server.name}: {message}'})
        else:
            # Restore original values on failure
            for key, value in original_values.items():
                setattr(project, key, value)
            return jsonify({'success': False, 'error': message})
            
    except Exception as e:
        # Restore original values on exception
        for key, value in original_values.items():
            setattr(project, key, value)
        return jsonify({'success': False, 'error': str(e)})

@app.route('/system-logs')
@login_required
def system_logs():
    if not current_user.has_permission('server_operations'):
        flash('Access denied. Technical Agent privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Get filter parameters
    search = request.args.get('search', '')
    log_type_filter = request.args.get('log_type', '')
    server_filter = request.args.get('server', '')
    status_filter = request.args.get('status', '')
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Filter system updates, backups, and servers by user's access
    if current_user.is_admin:
        accessible_server_ids = [s.id for s in HetznerServer.query.all()]
        servers = HetznerServer.query.all()
    else:
        accessible_servers = current_user.get_accessible_servers()
        accessible_server_ids = [s.id for s in accessible_servers]
        servers = accessible_servers
    
    # Base queries
    updates_query = SystemUpdate.query
    backups_query = DatabaseBackup.query
    
    if not current_user.is_admin and accessible_server_ids:
        updates_query = updates_query.filter(SystemUpdate.server_id.in_(accessible_server_ids))
        backups_query = backups_query.filter(DatabaseBackup.server_id.in_(accessible_server_ids))
    elif not current_user.is_admin:
        updates_query = SystemUpdate.query.filter(False)
        backups_query = DatabaseBackup.query.filter(False)
    
    # Apply filters
    if search:
        updates_query = updates_query.join(HetznerServer).filter(
            db.or_(
                HetznerServer.name.ilike(f'%{search}%'),
                SystemUpdate.update_description.ilike(f'%{search}%')
            )
        )
        backups_query = backups_query.join(HetznerServer).filter(
            db.or_(
                HetznerServer.name.ilike(f'%{search}%'),
                DatabaseBackup.database_name.ilike(f'%{search}%')
            )
        )
    
    if server_filter:
        updates_query = updates_query.filter(SystemUpdate.server_id == server_filter)
        backups_query = backups_query.filter(DatabaseBackup.server_id == server_filter)
    
    if status_filter:
        updates_query = updates_query.filter(SystemUpdate.status == status_filter)
        backups_query = backups_query.filter(DatabaseBackup.status == status_filter)
    
    # Determine which logs to show based on log_type filter
    if log_type_filter == 'deployment':
        updates = updates_query.order_by(SystemUpdate.started_at.desc()).limit(50).all()
        backups = []
    elif log_type_filter == 'backup':
        updates = []
        backups = backups_query.order_by(DatabaseBackup.started_at.desc()).limit(50).all()
    else:
        updates = updates_query.order_by(SystemUpdate.started_at.desc()).limit(50).all()
        backups = backups_query.order_by(DatabaseBackup.started_at.desc()).limit(50).all()
    
    if is_ajax:
        updates_data = []
        for update in updates:
            duration = None
            if update.completed_at and update.started_at:
                duration = int((update.completed_at - update.started_at).total_seconds())
            
            updates_data.append({
                'id': update.id,
                'server_name': update.server.name if update.server else 'Unknown',
                'server_ip': update.server.public_ip if update.server else 'N/A',
                'update_type': update.update_type,
                'status': update.status,
                'started_at': update.started_at.strftime('%Y-%m-%d %H:%M:%S'),
                'duration': duration,
                'initiated_by': update.initiated_by_user.username if update.initiated_by_user else 'System',
                'type': 'deployment'
            })
        
        backups_data = []
        for backup in backups:
            backups_data.append({
                'id': backup.id,
                'database_name': backup.database_name,
                'server_name': backup.server.name if backup.server else 'Local',
                'backup_type': backup.backup_type,
                'status': backup.status,
                'started_at': backup.started_at.strftime('%Y-%m-%d %H:%M:%S'),
                'file_size': backup.file_size,
                'initiated_by': backup.initiated_by_user.username if backup.initiated_by_user else 'System',
                'type': 'backup'
            })
        
        return jsonify({
            'success': True,
            'updates': updates_data,
            'backups': backups_data,
            'total_shown': len(updates_data) + len(backups_data)
        })
    
    return render_template('system_logs.html', 
                         updates=updates, 
                         backups=backups, 
                         servers=servers)

@app.route('/api/logs/<log_type>/<int:log_id>')
@login_required
def get_log_details(log_type, log_id):
    if not current_user.has_permission('server_operations'):
        return jsonify({'error': 'Access denied'}), 403
    
    if log_type == 'update':
        log = SystemUpdate.query.get_or_404(log_id)
        return jsonify({
            'description': log.update_description,
            'execution_log': log.execution_log,
            'error_log': log.error_log,
            'status': log.status,
            'started_at': log.started_at.isoformat() if log.started_at else None,
            'completed_at': log.completed_at.isoformat() if log.completed_at else None
        })
    elif log_type == 'backup':
        log = DatabaseBackup.query.get_or_404(log_id)
        return jsonify({
            'description': f"{log.backup_type} backup of {log.database_name}",
            'execution_log': getattr(log, 'execution_log', 'Backup process completed'),
            'error_log': getattr(log, 'error_log', None),
            'status': log.status,
            'started_at': log.started_at.isoformat() if log.started_at else None,
            'completed_at': log.completed_at.isoformat() if log.completed_at else None
        })
    else:
        return jsonify({'error': 'Invalid log type'}), 400

@app.route('/api/logs/<log_type>/<int:log_id>/download')
@login_required
def download_log_file(log_type, log_id):
    if not current_user.has_permission('server_operations'):
        flash('Access denied. Technical Agent privileges required.', 'danger')
        return redirect(url_for('index'))
    
    if log_type == 'update':
        log = SystemUpdate.query.get_or_404(log_id)
        filename = f"deployment_log_{log.update_id}_{log.started_at.strftime('%Y%m%d_%H%M%S')}.txt"
        content = f"Deployment Log - {log.update_description}\n"
        content += f"Started: {log.started_at}\n"
        content += f"Status: {log.status}\n"
        content += f"Completed: {log.completed_at}\n\n"
        content += "=== EXECUTION LOG ===\n"
        content += log.execution_log or "No execution logs available"
        if log.error_log:
            content += "\n\n=== ERROR LOG ===\n"
            content += log.error_log
            
    elif log_type == 'backup':
        log = DatabaseBackup.query.get_or_404(log_id)
        filename = f"backup_log_{log.backup_id}_{log.started_at.strftime('%Y%m%d_%H%M%S')}.txt"
        content = f"Backup Log - {log.database_name}\n"
        content += f"Type: {log.backup_type}\n"
        content += f"Started: {log.started_at}\n"
        content += f"Status: {log.status}\n"
        content += f"Completed: {log.completed_at}\n\n"
        content += "=== BACKUP LOG ===\n"
        content += getattr(log, 'execution_log', 'Backup completed successfully')
    else:
        flash('Invalid log type', 'danger')
        return redirect(url_for('system_logs'))
    
    response = make_response(content)
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    response.headers["Content-type"] = "text/plain"
    return response

@app.route('/backups')
@login_required
def backups():
    if not current_user.has_permission('database_operations'):
        flash('Access denied. Technical Agent privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Get filter parameters
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    server_filter = request.args.get('server', '')
    backup_type_filter = request.args.get('backup_type', '')
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Filter backups by user's accessible servers
    if current_user.is_admin:
        query = DatabaseBackup.query
    else:
        accessible_servers = current_user.get_accessible_servers()
        accessible_server_ids = [s.id for s in accessible_servers]
        query = DatabaseBackup.query.filter(
            DatabaseBackup.server_id.in_(accessible_server_ids)
        ) if accessible_server_ids else DatabaseBackup.query.filter(False)
    
    # Apply filters
    if search:
        query = query.join(HetznerServer).filter(
            db.or_(
                DatabaseBackup.database_name.ilike(f'%{search}%'),
                HetznerServer.name.ilike(f'%{search}%')
            )
        )
    
    if status_filter:
        query = query.filter(DatabaseBackup.status == status_filter)
    
    if server_filter:
        query = query.filter(DatabaseBackup.server_id == server_filter)
    
    if backup_type_filter:
        query = query.filter(DatabaseBackup.backup_type == backup_type_filter)
    
    backups = query.order_by(DatabaseBackup.started_at.desc()).all()
    
    # Get available servers for filter dropdown
    if current_user.is_admin:
        servers = HetznerServer.query.all()
    else:
        servers = current_user.get_accessible_servers()
    
    if is_ajax:
        backups_data = []
        for backup in backups:
            backups_data.append({
                'id': backup.id,
                'database_name': backup.database_name,
                'server_name': backup.server.name if backup.server else 'Local Server',
                'backup_type': backup.backup_type,
                'status': backup.status,
                'file_size': backup.file_size,
                'started_at': backup.started_at.strftime('%Y-%m-%d %H:%M'),
                'completed_at': backup.completed_at.strftime('%Y-%m-%d %H:%M') if backup.completed_at else None
            })
        
        return jsonify({
            'success': True,
            'backups': backups_data,
            'total_shown': len(backups_data),
            'stats': {
                'total': len(backups_data),
                'completed': len([b for b in backups if b.status == 'completed']),
                'running': len([b for b in backups if b.status == 'running']),
                'failed': len([b for b in backups if b.status == 'failed'])
            }
        })
    
    return render_template('backups.html', backups=backups, servers=servers)

@app.route('/system-updates')
@login_required
def system_updates():
    if not current_user.has_permission('system_updates'):
        flash('Access denied. Technical Agent privileges required.', 'danger')
        return redirect(url_for('index'))
    
    updates = SystemUpdate.query.order_by(SystemUpdate.started_at.desc()).all()
    return render_template('system_updates.html', updates=updates)

# Project access management has been removed - tech managers are now assigned directly to projects

# User Management Routes (Admin Only) - Simplified for user approval and role assignment
@app.route('/admin/user-management')
@login_required
def user_management():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Get filter parameters
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')
    
    # Build query
    query = User.query
    
    if role_filter:
        from models import UserRole
        if role_filter == 'admin':
            query = query.filter(User.role == UserRole.ADMIN)
        elif role_filter == 'sales_agent':
            query = query.filter(User.role == UserRole.SALES_AGENT)
        elif role_filter == 'technical_agent':
            query = query.filter(User.role == UserRole.TECHNICAL_AGENT)
    if status_filter:
        if status_filter == 'approved':
            query = query.filter(User.is_approved == True)
        elif status_filter == 'pending':
            query = query.filter(User.is_approved == False)
    if search:
        query = query.filter(
            db.or_(
                User.username.contains(search),
                User.email.contains(search)
            )
        )
    
    all_users = query.order_by(User.created_at.desc()).all()
    
    # Get user statistics
    total_users = User.query.all()
    stats = {
        'total_users': len(total_users),
        'approved': len([u for u in total_users if u.is_approved]),
        'pending': len([u for u in total_users if not u.is_approved]),
        'admins': len([u for u in total_users if u.is_admin]),
        'technical': len([u for u in total_users if u.is_technical_agent]),
        'sales': len([u for u in total_users if u.is_sales_agent])
    }
    
    # Check if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'users': [{
                'id': u.id,
                'username': u.username,
                'email': u.email,
                'role': u.role.value if u.role else 'unknown',
                'is_manager': u.is_manager,
                'is_approved': u.is_approved,
                'is_admin': u.is_admin,
                'is_technical_agent': u.is_technical_agent,
                'is_sales_agent': u.is_sales_agent,
                'created_at': u.created_at.strftime('%Y-%m-%d') if u.created_at else 'Unknown'
            } for u in all_users],
            'stats': stats,
            'total_shown': len(all_users)
        })
    
    return render_template('user_management.html', users=all_users, stats=stats,
                         role_filter=role_filter, status_filter=status_filter, search=search)

# Approve User Route
@app.route('/admin/approve-user', methods=['POST'])
@login_required
def approve_user():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    user_id = request.form.get('user_id')
    user = User.query.get(user_id)
    
    if user:
        user.is_approved = True
        db.session.commit()
        flash(f'User {user.username} has been approved successfully.', 'success')
    else:
        flash('User not found.', 'danger')
    
    return redirect(url_for('user_management'))

# Change User Role Route
@app.route('/admin/change-user-role', methods=['POST'])
@login_required
def change_user_role():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    user_id = request.form.get('user_id')
    new_role = request.form.get('new_role')
    is_manager = request.form.get('is_manager') == 'on'
    
    user = User.query.get(user_id)
    
    if user:
        # Validate role
        if new_role in ['admin', 'sales_agent', 'technical_agent']:
            user.role = UserRole(new_role)
            
            # Set manager flag only for technical agents
            if new_role == 'technical_agent':
                user.is_manager = is_manager
            else:
                user.is_manager = False
            
            # Auto-approve user when assigning role
            user.is_approved = True
            
            db.session.commit()
            flash(f'Role changed successfully for {user.username} to {new_role.replace("_", " ").title()}.', 'success')
        else:
            flash('Invalid role selected.', 'danger')
    else:
        flash('User not found.', 'danger')
    
    return redirect(url_for('user_management'))

# Delete User Route
@app.route('/admin/delete-user', methods=['POST'])
@login_required
def delete_user():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    user_id = request.form.get('user_id')
    user = User.query.get(user_id)
    
    if user:
        if user.id == current_user.id:
            flash('You cannot delete your own account.', 'danger')
        else:
            username = user.username
            
            try:
                # Delete related records first to avoid foreign key constraints
                # Delete user project access records
                UserProjectAccess.query.filter_by(user_id=user.id).delete()
                
                # Delete user server access records
                UserServerAccess.query.filter_by(user_id=user.id).delete()
                
                # Delete notifications for this user
                Notification.query.filter_by(user_id=user.id).delete()
                
                # Delete server requests created by this user
                ServerRequest.query.filter_by(user_id=user.id).delete()
                
                # Delete deployment executions by this user
                DeploymentExecution.query.filter_by(executed_by=user.id).delete()
                
                # Delete database backups initiated by this user
                DatabaseBackup.query.filter_by(initiated_by=user.id).delete()
                
                # Delete system updates initiated by this user
                SystemUpdate.query.filter_by(initiated_by=user.id).delete()
                
                # Now delete the user
                db.session.delete(user)
                db.session.commit()
                
                flash(f'User {username} and all related records have been deleted successfully.', 'success')
                
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error deleting user {username}: {str(e)}")
                flash(f'Error deleting user {username}. Please try again.', 'danger')
    else:
        flash('User not found.', 'danger')
    
    return redirect(url_for('user_management'))

# Server Assignment Routes (Admin and Technical Managers Only)
@app.route('/admin/server-assignments')
@login_required
def server_assignments():
    # Check if user is admin or technical manager
    if not (current_user.is_admin or (current_user.role == UserRole.TECHNICAL_AGENT and current_user.is_manager)):
        flash('Access denied. Admin or Technical Manager privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Get servers based on user's access level
    if current_user.is_admin:
        # Admins can assign any server
        servers = HetznerServer.query.all()
    else:
        # Tech managers can only assign servers from their accessible projects
        servers = current_user.get_accessible_servers()
    
    # Get only normal technical agents (not managers) for assignment
    # Tech managers get automatic project access and don't need individual server assignments
    technical_users = User.query.filter_by(role=UserRole.TECHNICAL_AGENT, is_manager=False).all()
    
    return render_template('server_assignments.html', servers=servers, technical_users=technical_users)

@app.route('/admin/assign-user-to-server', methods=['POST'])
@login_required
def assign_user_to_server():
    # Check if user is admin or technical manager
    if not (current_user.is_admin or (current_user.role == UserRole.TECHNICAL_AGENT and current_user.is_manager)):
        flash('Access denied. Admin or Technical Manager privileges required.', 'danger')
        return redirect(url_for('index'))
    
    server_id = request.form.get('server_id')
    user_ids = request.form.getlist('user_ids')  # Get multiple user IDs
    access_level = request.form.get('access_level')
    
    # Validate server
    server = HetznerServer.query.get(server_id)
    if not server:
        flash('Invalid server selected.', 'danger')
        return redirect(url_for('server_assignments'))
    
    if not user_ids:
        flash('Please select at least one technical agent.', 'warning')
        return redirect(url_for('server_assignments'))
    
    # Track assignment results
    assigned_users = []
    already_assigned = []
    invalid_users = []
    
    # Process each selected user
    for user_id in user_ids:
        user = User.query.get(user_id)
        if not user:
            invalid_users.append(f"User ID {user_id}")
            continue
            
        # Check if assignment already exists
        existing = UserServerAccess.query.filter_by(user_id=user_id, server_id=server_id).first()
        if existing:
            already_assigned.append(user.username)
            continue
        
        # Create new assignment
        assignment = UserServerAccess()
        assignment.user_id = user_id
        assignment.server_id = server_id
        assignment.access_level = access_level
        assignment.assigned_by = current_user.id
        
        db.session.add(assignment)
        assigned_users.append(user.username)
    
    # Commit all changes
    if assigned_users:
        db.session.commit()
        
    # Build success/warning messages
    messages = []
    if assigned_users:
        if len(assigned_users) == 1:
            messages.append(f'Successfully assigned {assigned_users[0]} to server {server.name} with {access_level} access.')
        else:
            messages.append(f'Successfully assigned {len(assigned_users)} users to server {server.name}: {", ".join(assigned_users)}')
        
    if already_assigned:
        if len(already_assigned) == 1:
            messages.append(f'User {already_assigned[0]} was already assigned to this server.')
        else:
            messages.append(f'{len(already_assigned)} users were already assigned: {", ".join(already_assigned)}')
            
    if invalid_users:
        messages.append(f'Invalid users skipped: {", ".join(invalid_users)}')
    
    # Flash appropriate message
    if assigned_users:
        flash(' '.join(messages), 'success')
    elif already_assigned and not invalid_users:
        flash(' '.join(messages), 'warning') 
    else:
        flash(' '.join(messages), 'danger')
        
    return redirect(url_for('server_assignments'))

@app.route('/admin/remove-server-assignment', methods=['POST'])
@login_required
def remove_server_assignment():
    # Check if user is admin or technical manager
    if not (current_user.is_admin or (current_user.role == UserRole.TECHNICAL_AGENT and current_user.is_manager)):
        flash('Access denied. Admin or Technical Manager privileges required.', 'danger')
        return redirect(url_for('index'))
    
    assignment_id = request.form.get('assignment_id')
    assignment = UserServerAccess.query.get(assignment_id)
    
    if assignment:
        username = assignment.user.username
        server_name = assignment.server.name
        db.session.delete(assignment)
        db.session.commit()
        flash(f'Removed server assignment for {username} from {server_name}.', 'success')
    else:
        flash('Assignment not found.', 'danger')
    
    return redirect(url_for('server_assignments'))

@app.route('/admin/promote-to-manager', methods=['POST'])
@login_required 
def promote_to_manager():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    user_id = request.form.get('user_id')
    user = User.query.get(user_id)
    
    if not user or user.role != UserRole.TECHNICAL_AGENT:
        flash('Invalid technical user selected.', 'danger')
        return redirect(url_for('user_management'))
    
    if user.is_manager:
        flash(f'{user.username} is already a technical manager.', 'info')
        return redirect(url_for('user_management'))
    
    # Promote user to manager
    user.is_manager = True
    db.session.commit()
    
    flash(f'{user.username} has been promoted to Technical Manager with access to all servers and projects.', 'success')
    return redirect(url_for('user_assignments'))


# Project Tech Manager Assignment Routes (Admin Only)
@app.route('/assign-manager-to-project', methods=['POST'])
@login_required
def assign_manager_to_project():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    user_id = request.form.get('user_id')
    project_id = request.form.get('project_id')
    
    user = User.query.get(user_id)
    project = HetznerProject.query.get(project_id)
    
    if not user or not project:
        flash('Invalid user or project selected.', 'danger')
        return redirect(url_for('hetzner_project_detail', project_id=project_id))
    
    if not (user.role == UserRole.TECHNICAL_AGENT and user.is_manager):
        flash('Selected user is not a tech manager.', 'danger')
        return redirect(url_for('hetzner_project_detail', project_id=project_id))
    
    # Check if already assigned
    existing = UserProjectAccess.query.filter_by(user_id=user_id, project_id=project_id).first()
    if existing:
        flash(f'{user.username} is already assigned to project {project.name}.', 'info')
        return redirect(url_for('hetzner_project_detail', project_id=project_id))
    
    # Create assignment
    assignment = UserProjectAccess()
    assignment.user_id = user_id
    assignment.project_id = project_id
    assignment.access_level = 'admin'  # Tech managers get admin access to projects
    assignment.granted_by = current_user.id
    
    db.session.add(assignment)
    db.session.commit()
    
    flash(f'Successfully assigned {user.username} as tech manager for project {project.name}.', 'success')
    return redirect(url_for('hetzner_project_detail', project_id=project_id))

@app.route('/remove-manager-from-project', methods=['POST'])
@login_required
def remove_manager_from_project():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    user_id = request.form.get('user_id')
    project_id = request.form.get('project_id')
    
    assignment = UserProjectAccess.query.filter_by(user_id=user_id, project_id=project_id).first()
    
    if assignment:
        user = User.query.get(user_id)
        project = HetznerProject.query.get(project_id)
        
        db.session.delete(assignment)
        db.session.commit()
        
        flash(f'Removed {user.username} from project {project.name}.', 'success')
    else:
        flash('Assignment not found.', 'danger')
    
    return redirect(url_for('hetzner_project_detail', project_id=project_id))

# Hetzner Project Management Routes (Admin Only)
@app.route('/hetzner-projects')
@login_required
def hetzner_projects():
    # Allow technical agents to see their assigned projects
    if not (current_user.is_admin or current_user.is_technical_agent):
        flash('Access denied. Technical Agent or Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Use the user's get_accessible_projects method which handles permissions correctly
    projects = current_user.get_accessible_projects()
    return render_template('hetzner_projects.html', projects=projects)

@app.route('/hetzner-projects/<int:project_id>')
@login_required
def hetzner_project_detail(project_id):
    # Allow technical agents to see their assigned projects
    if not (current_user.is_admin or current_user.is_technical_agent):
        flash('Access denied. Technical Agent or Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    project = HetznerProject.query.get_or_404(project_id)
    
    # Check if technical user has access to this specific project
    if current_user.is_technical_agent and not current_user.is_admin:
        accessible_project_ids = [p.id for p in current_user.get_accessible_projects()]
        if project_id not in accessible_project_ids:
            flash('Access denied. You do not have permission to view this project.', 'danger')
            return redirect(url_for('hetzner_projects'))
    
    servers = HetznerServer.query.filter_by(project_id=project_id).all()
    
    # Get tech managers assigned to this project and available tech managers for assignment
    tech_managers = User.query.filter_by(role=UserRole.TECHNICAL_AGENT, is_manager=True).all()
    assigned_managers = User.query.join(UserProjectAccess, User.id == UserProjectAccess.user_id).filter(
        UserProjectAccess.project_id == project_id,
        User.role == UserRole.TECHNICAL_AGENT,
        User.is_manager == True
    ).all()
    available_managers = [m for m in tech_managers if m not in assigned_managers]
    
    return render_template('hetzner_project_detail.html', 
                         project=project, 
                         servers=servers,
                         assigned_managers=assigned_managers,
                         available_managers=available_managers)

@app.route('/hetzner-projects/<int:project_id>/sync', methods=['POST'])
@login_required
def sync_project_servers(project_id):
    # Allow technical agents to sync their assigned projects
    if not (current_user.is_admin or current_user.is_technical_agent):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Access denied. Technical Agent or Admin privileges required.'}), 403
        flash('Access denied. Technical Agent or Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Check if technical user has access to this specific project
    if current_user.is_technical_agent and not current_user.is_admin:
        accessible_project_ids = [p.id for p in current_user.get_accessible_projects()]
        if project_id not in accessible_project_ids:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': 'Access denied. You do not have permission to sync this project.'}), 403
            flash('Access denied. You do not have permission to sync this project.', 'danger')
            return redirect(url_for('hetzner_projects'))
    
    project = HetznerProject.query.get_or_404(project_id)
    
    try:
        hetzner_service = HetznerService(project_id=project_id)
        result = hetzner_service.sync_servers_from_hetzner()
        
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': f'Sync completed! {result["synced"]} new servers, {result["updated"]} updated, {result.get("deleted", 0)} deleted, {result["total"]} total.',
                    'synced': result["synced"],
                    'updated': result["updated"],
                    'deleted': result.get("deleted", 0),
                    'total': result["total"],
                    'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result["error"]
                })
        else:
            # Regular form submission
            if result['success']:
                flash(f'Sync completed! {result["synced"]} new servers, {result["updated"]} updated, {result["total"]} total.', 'success')
            else:
                flash(f'Sync failed: {result["error"]}', 'danger')
                
    except Exception as e:
        error_msg = f'Error during sync: {str(e)}'
        
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'error': error_msg
            })
        else:
            flash(error_msg, 'danger')
    
    return redirect(url_for('hetzner_project_detail', project_id=project_id))

@app.route('/hetzner-projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_hetzner_project(project_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    project = HetznerProject.query.get_or_404(project_id)
    
    if request.method == 'POST':
        project.name = request.form['name']
        project.description = request.form['description']
        project.hetzner_api_token = request.form['hetzner_api_token']
        project.max_servers = int(request.form['max_servers'])
        project.monthly_budget = float(request.form['monthly_budget']) if request.form['monthly_budget'] else None
        project.is_active = 'is_active' in request.form
        project.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Project updated successfully!', 'success')
        return redirect(url_for('hetzner_project_detail', project_id=project_id))
    
    return render_template('edit_hetzner_project.html', project=project)

@app.route('/hetzner-projects/new', methods=['GET', 'POST'])
@login_required
def new_hetzner_project():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        project = HetznerProject(
            name=request.form['name'],
            description=request.form['description'],
            hetzner_api_token=request.form['hetzner_api_token'],
            max_servers=int(request.form['max_servers']),
            monthly_budget=float(request.form['monthly_budget']) if request.form['monthly_budget'] else None,
            created_by=current_user.id
        )
        
        db.session.add(project)
        db.session.commit()
        
        flash(f'Project "{project.name}" created successfully!', 'success')
        return redirect(url_for('hetzner_projects'))
    
    return render_template('new_hetzner_project.html')

@app.route('/sync-all-projects', methods=['POST'])
@login_required
def sync_all_projects():
    if not current_user.is_admin:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Access denied. Admin privileges required.'}), 403
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    projects = HetznerProject.query.filter_by(is_active=True).all()
    total_synced = 0
    total_updated = 0
    total_deleted = 0
    errors = []
    
    for project in projects:
        try:
            hetzner_service = HetznerService(project_id=project.id)
            result = hetzner_service.sync_servers_from_hetzner()
            
            if result['success']:
                total_synced += result['synced']
                total_updated += result['updated']
                total_deleted += result.get('deleted', 0)
            else:
                errors.append(f'{project.name}: {result["error"]}')
        except Exception as e:
            errors.append(f'{project.name}: {str(e)}')
    
    # Check if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if errors:
            return jsonify({
                'success': False,
                'error': f'Sync completed with errors. Synced: {total_synced}, Updated: {total_updated}, Deleted: {total_deleted}. Errors: {", ".join(errors)}'
            })
        else:
            return jsonify({
                'success': True,
                'message': f'All projects synced successfully! {total_synced} new servers, {total_updated} updated, {total_deleted} deleted.',
                'synced': total_synced,
                'updated': total_updated,
                'deleted': total_deleted,
                'projects_count': len(projects),
                'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            })
    else:
        # Regular form submission
        if errors:
            flash(f'Sync completed with errors. Synced: {total_synced}, Updated: {total_updated}, Deleted: {total_deleted}. Errors: {", ".join(errors)}', 'warning')
        else:
            flash(f'All projects synced successfully! {total_synced} new servers, {total_updated} updated, {total_deleted} deleted.', 'success')
        
        return redirect(url_for('hetzner_projects'))
