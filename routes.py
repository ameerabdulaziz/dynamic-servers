import random
import time
import os
import subprocess
from pathlib import Path
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify, make_response, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from app import app, db
from models import User, UserRole, ServerRequest, Notification, HetznerServer, DeploymentScript, DeploymentExecution, ClientSubscription, DatabaseBackup, SystemUpdate, HetznerProject, UserProjectAccess, UserServerAccess
from forms import LoginForm, RegistrationForm, ServerRequestForm, AdminReviewForm, DeploymentScriptForm, ExecuteDeploymentForm, ServerManagementForm
from hetzner_service import HetznerService
from ansible_service import AnsibleService
from ssh_service import SSHService, get_default_deploy_script, get_default_backup_script

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
    
    # Check for system backup files
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
    if server_backup_root.exists():
        # Go through each server directory
        for server_dir in server_backup_root.iterdir():
            if server_dir.is_dir():
                server_name = server_dir.name
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
                ServerRequest.server_name.contains(search),
                ServerRequest.application_name.contains(search),
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
    
    return render_template('admin_dashboard.html', requests=requests, stats=stats, 
                         status_filter=status_filter, priority_filter=priority_filter, search=search)

@app.route('/technical-dashboard')
@login_required
def technical_dashboard():
    if not current_user.has_permission('manage_servers'):
        flash('Access denied. Technical Agent privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Admins see all servers and data - no filtering applied
    if current_user.is_admin or (current_user.role == UserRole.TECHNICAL_AGENT and current_user.is_manager):
        # Admins and manager technical agents see all servers
        servers = HetznerServer.query.all()
        # Get all system updates, backups, and deployments
        recent_updates = SystemUpdate.query.order_by(SystemUpdate.started_at.desc()).limit(10).all()
        recent_backups = DatabaseBackup.query.order_by(DatabaseBackup.started_at.desc()).limit(10).all()
        recent_deployments = DeploymentExecution.query.order_by(DeploymentExecution.started_at.desc()).limit(10).all()
    else:
        # Regular technical agents see only servers they are specifically assigned to via UserServerAccess
        assigned_server_access = UserServerAccess.query.filter_by(user_id=current_user.id).all()
        accessible_server_ids = [access.server_id for access in assigned_server_access]
        servers = HetznerServer.query.filter(HetznerServer.id.in_(accessible_server_ids)).all() if accessible_server_ids else []
        
        # Filter activities to only show data from servers they are specifically assigned to
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
    if form.validate_on_submit():
        server_request = ServerRequest()
        server_request.user_id = current_user.id
        server_request.server_name = form.server_name.data
        server_request.server_type = form.server_type.data
        server_request.cpu_cores = form.cpu_cores.data
        server_request.memory_gb = form.memory_gb.data
        server_request.storage_gb = form.storage_gb.data
        server_request.operating_system = form.operating_system.data
        server_request.application_name = form.application_name.data
        server_request.application_type = form.application_type.data
        server_request.application_description = form.application_description.data
        server_request.business_justification = form.business_justification.data
        server_request.estimated_usage = form.estimated_usage.data
        server_request.priority = form.priority.data
        db.session.add(server_request)
        db.session.commit()
        
        # Create notification for user
        notification = Notification()
        notification.user_id = current_user.id
        notification.title = 'Server Request Submitted'
        notification.message = f'Your server request "{server_request.server_name}" has been submitted and is pending approval.'
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
        
        # If approved, redirect to deployment
        if form.status.data == 'approved':
            return redirect(url_for('deploy_server', request_id=request_id))
    
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

# Server Management Routes

@app.route('/servers')
@login_required
def servers_list():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Get servers from database
    servers = HetznerServer.query.order_by(HetznerServer.last_synced.desc()).all()
    
    # Get server statistics
    stats = {
        'total_servers': len(servers),
        'running': len([s for s in servers if s.status == 'running']),
        'stopped': len([s for s in servers if s.status == 'stopped']),
        'deploying': len([s for s in servers if s.deployment_status == 'deploying'])
    }
    
    return render_template('servers_list.html', servers=servers, stats=stats)

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
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    server = HetznerServer.query.get_or_404(server_id)
    
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
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    server = HetznerServer.query.get_or_404(server_id)
    form = ServerManagementForm()
    
    if form.validate_on_submit():
        try:
            hetzner_service = HetznerService()
            
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
                # Update server status (will be synced properly on next sync)
                if form.action.data == 'start':
                    server.status = 'starting'
                elif form.action.data == 'stop':
                    server.status = 'stopping'
                elif form.action.data == 'reboot':
                    server.status = 'rebooting'
                db.session.commit()
            else:
                flash(f'Error executing {form.action.data}: {result["error"]}', 'danger')
                
        except Exception as e:
            flash(f'Error managing server: {str(e)}', 'danger')
    
    return redirect(url_for('server_detail', server_id=server_id))

@app.route('/servers/<int:server_id>/deploy', methods=['POST'])
@login_required
def deploy_to_server(server_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    server = HetznerServer.query.get_or_404(server_id)
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
    
    # Admins have complete system access - see all servers
    if current_user.is_admin or (current_user.role == UserRole.TECHNICAL_AGENT and current_user.is_manager):
        # Admins and manager technical agents see all servers
        servers = HetznerServer.query.all()
    else:
        # Regular technical agents see only servers they are specifically assigned to via UserServerAccess
        assigned_server_access = UserServerAccess.query.filter_by(user_id=current_user.id).all()
        accessible_server_ids = [access.server_id for access in assigned_server_access]
        servers = HetznerServer.query.filter(HetznerServer.id.in_(accessible_server_ids)).all() if accessible_server_ids else []
    
    return render_template('server_operations.html', servers=servers)

@app.route('/server/<int:server_id>/backup', methods=['POST'])
@login_required
def create_backup(server_id):
    if not current_user.has_permission('database_operations'):
        flash('Access denied. Technical Agent privileges required.', 'danger')
        return redirect(url_for('index'))
    
    server = HetznerServer.query.get_or_404(server_id)
    
    # Check if user has access to this specific server (admins and managers have full access)
    if not (current_user.is_admin or (current_user.role == UserRole.TECHNICAL_AGENT and current_user.is_manager)):
        # Regular technical agents need specific server access
        server_access = UserServerAccess.query.filter_by(user_id=current_user.id, server_id=server_id).first()
        if not server_access or server_access.access_level not in ['write', 'admin']:
            flash('Access denied. You do not have write access to this server.', 'danger')
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
            flash(f'Project {server.project.name if server.project else "Unknown"} requires SSH key configuration for remote backup execution', 'warning')
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
    
    # Check if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': backup.status == 'completed',
            'message': f'Backup {"completed" if backup.status == "completed" else "failed"}',
            'timestamp': backup.completed_at.strftime('%Y-%m-%d %H:%M') if backup.completed_at else None,
            'status': backup.status
        })
    
    return redirect(url_for('server_operations'))

@app.route('/server/<int:server_id>/update', methods=['POST'])
@login_required
def create_system_update(server_id):
    if not current_user.has_permission('system_updates'):
        flash('Access denied. Technical Agent privileges required.', 'danger')
        return redirect(url_for('index'))
    
    server = HetznerServer.query.get_or_404(server_id)
    
    # Check if user has access to this specific server (admins and managers have full access)
    if not (current_user.is_admin or (current_user.role == UserRole.TECHNICAL_AGENT and current_user.is_manager)):
        # Regular technical agents need specific server access
        server_access = UserServerAccess.query.filter_by(user_id=current_user.id, server_id=server_id).first()
        if not server_access or server_access.access_level not in ['write', 'admin']:
            flash('Access denied. You do not have write access to this server.', 'danger')
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
            flash(f'Project {server.project.name if server.project else "Unknown"} requires SSH key configuration for remote script execution', 'warning')
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
    
    # Check if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': update.status == 'completed',
            'message': f'Update {"completed" if update.status == "completed" else "failed"}',
            'timestamp': update.completed_at.strftime('%Y-%m-%d %H:%M') if update.completed_at else None,
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
    
    # Get all system updates and backups for logging
    updates = SystemUpdate.query.order_by(SystemUpdate.started_at.desc()).limit(50).all()
    backups = DatabaseBackup.query.order_by(DatabaseBackup.started_at.desc()).limit(50).all()
    servers = HetznerServer.query.all()
    
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
    
    backups = DatabaseBackup.query.order_by(DatabaseBackup.started_at.desc()).all()
    return render_template('backups.html', backups=backups)

@app.route('/system-updates')
@login_required
def system_updates():
    if not current_user.has_permission('system_updates'):
        flash('Access denied. Technical Agent privileges required.', 'danger')
        return redirect(url_for('index'))
    
    updates = SystemUpdate.query.order_by(SystemUpdate.started_at.desc()).all()
    return render_template('system_updates.html', updates=updates)

# Project Access Management Routes (Admin Only)
@app.route('/project-access')
@login_required
def project_access():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Get all users and their project access
    users = User.query.filter(User.role != UserRole.ADMIN).all()
    projects = HetznerProject.query.all()
    
    # Build access matrix - organized by user for easier display
    access_matrix = {}
    for user in users:
        access_matrix[user.id] = {
            'user': user,
            'project_access': {}
        }
        for project in projects:
            access = UserProjectAccess.query.filter_by(user_id=user.id, project_id=project.id).first()
            access_matrix[user.id]['project_access'][project.id] = access
    
    return render_template('project_access.html', 
                         access_matrix=access_matrix, 
                         projects=projects)

@app.route('/project-access/grant', methods=['POST'])
@login_required
def grant_project_access():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    user_id = request.form.get('user_id')
    project_id = request.form.get('project_id')
    access_level = request.form.get('access_level', 'read')
    
    # Check if access already exists
    existing = UserProjectAccess.query.filter_by(user_id=user_id, project_id=project_id).first()
    
    if existing:
        existing.access_level = access_level
        existing.granted_by = current_user.id
    else:
        access = UserProjectAccess()
        access.user_id = user_id
        access.project_id = project_id
        access.access_level = access_level
        access.granted_by = current_user.id
        db.session.add(access)
    
    user = User.query.get(user_id)
    project = HetznerProject.query.get(project_id)
    
    db.session.commit()
    flash(f'Granted {access_level} access to {user.username} for project {project.name}', 'success')
    
    return redirect(url_for('project_access'))

@app.route('/project-access/revoke', methods=['POST'])
@login_required
def revoke_project_access():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    user_id = request.form.get('user_id')
    project_id = request.form.get('project_id')
    
    access = UserProjectAccess.query.filter_by(user_id=user_id, project_id=project_id).first()
    
    if access:
        user = User.query.get(user_id)
        project = HetznerProject.query.get(project_id)
        db.session.delete(access)
        db.session.commit()
        flash(f'Revoked project access for {user.username} from {project.name}', 'success')
    
    return redirect(url_for('project_access'))

# User Management Routes (Admin Only) - Simplified for user approval and role assignment
@app.route('/admin/user-management')
@login_required
def user_management():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Get all users for management
    all_users = User.query.all()
    
    return render_template('user_management.html', users=all_users)

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
            db.session.delete(user)
            db.session.commit()
            flash(f'User {username} has been deleted successfully.', 'success')
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
    servers = HetznerServer.query.all()
    
    # Get all technical users for assignment
    technical_users = User.query.filter_by(role=UserRole.TECHNICAL_AGENT).all()
    
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
        return redirect(url_for('user_assignments'))
    
    if user.is_manager:
        flash(f'{user.username} is already a technical manager.', 'info')
        return redirect(url_for('user_assignments'))
    
    # Promote user to manager
    user.is_manager = True
    db.session.commit()
    
    flash(f'{user.username} has been promoted to Technical Manager with access to all servers and projects.', 'success')
    return redirect(url_for('user_assignments'))

@app.route('/admin/project-access/<int:access_id>/edit', methods=['POST'])
@login_required
def edit_project_access(access_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    access = UserProjectAccess.query.get_or_404(access_id)
    data = request.get_json()
    new_level = data.get('access_level')
    
    if new_level not in ['read', 'write', 'admin']:
        return jsonify({'success': False, 'error': 'Invalid access level'}), 400
    
    access.access_level = new_level
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Access level updated to {new_level}'})

@app.route('/admin/project-access/<int:access_id>/delete', methods=['POST'])
@login_required 
def delete_project_access(access_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    access = UserProjectAccess.query.get_or_404(access_id)
    user_name = access.user.username
    project_name = access.project.name
    
    db.session.delete(access)
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Removed {user_name}\'s access to {project_name}'})

# Hetzner Project Management Routes (Admin Only)
@app.route('/hetzner-projects')
@login_required
def hetzner_projects():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Use the user's get_accessible_projects method which handles permissions correctly
    projects = current_user.get_accessible_projects()
    return render_template('hetzner_projects.html', projects=projects)

@app.route('/hetzner-projects/<int:project_id>')
@login_required
def hetzner_project_detail(project_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    project = HetznerProject.query.get_or_404(project_id)
    servers = HetznerServer.query.filter_by(project_id=project_id).all()
    
    return render_template('hetzner_project_detail.html', project=project, servers=servers)

@app.route('/hetzner-projects/<int:project_id>/sync', methods=['POST'])
@login_required
def sync_project_servers(project_id):
    if not current_user.is_admin:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Access denied. Admin privileges required.'}), 403
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    project = HetznerProject.query.get_or_404(project_id)
    
    try:
        hetzner_service = HetznerService(project_id=project_id)
        result = hetzner_service.sync_servers_from_hetzner()
        
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': f'Sync completed! {result["synced"]} new servers, {result["updated"]} updated, {result["total"]} total.',
                    'synced': result["synced"],
                    'updated': result["updated"],
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
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    projects = HetznerProject.query.filter_by(is_active=True).all()
    total_synced = 0
    total_updated = 0
    errors = []
    
    for project in projects:
        try:
            hetzner_service = HetznerService(project_id=project.id)
            result = hetzner_service.sync_servers_from_hetzner()
            
            if result['success']:
                total_synced += result['synced']
                total_updated += result['updated']
            else:
                errors.append(f'{project.name}: {result["error"]}')
        except Exception as e:
            errors.append(f'{project.name}: {str(e)}')
    
    if errors:
        flash(f'Sync completed with errors. Synced: {total_synced}, Updated: {total_updated}. Errors: {", ".join(errors)}', 'warning')
    else:
        flash(f'All projects synced successfully! {total_synced} new servers, {total_updated} updated.', 'success')
    
    return redirect(url_for('hetzner_projects'))
