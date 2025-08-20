import random
import time
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from app import app, db
from models import User, ServerRequest, Notification
from forms import LoginForm, RegistrationForm, ServerRequestForm, AdminReviewForm

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('dashboard')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page)
        flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User()
        user.username = form.username.data
        user.email = form.email.data
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    # Get user's requests
    requests = ServerRequest.query.filter_by(user_id=current_user.id).order_by(ServerRequest.created_at.desc()).all()
    
    # Get unread notifications
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).limit(5).all()
    
    # Statistics
    stats = {
        'total_requests': len(requests),
        'pending': len([r for r in requests if r.status == 'pending']),
        'approved': len([r for r in requests if r.status in ['approved', 'deploying', 'deployed']]),
        'rejected': len([r for r in requests if r.status == 'rejected'])
    }
    
    return render_template('dashboard.html', requests=requests, notifications=notifications, stats=stats)

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
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

@app.route('/request-server', methods=['GET', 'POST'])
@login_required
def request_server():
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
        return redirect(url_for('dashboard'))
    
    return render_template('request_server.html', form=form)

@app.route('/request/<request_id>')
@login_required
def request_detail(request_id):
    server_request = ServerRequest.query.filter_by(request_id=request_id).first_or_404()
    
    # Check if user can view this request
    if not current_user.is_admin and server_request.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    form = AdminReviewForm() if current_user.is_admin else None
    
    return render_template('request_detail.html', request=server_request, form=form)

@app.route('/request/<request_id>/review', methods=['POST'])
@login_required
def review_request(request_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
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
        return redirect(url_for('dashboard'))
    
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
    return redirect(request.referrer or url_for('dashboard'))

@app.context_processor
def inject_user():
    return dict(current_user=current_user)
