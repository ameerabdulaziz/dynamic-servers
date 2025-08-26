from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with server requests - specify foreign_keys to avoid ambiguity
    requests = db.relationship('ServerRequest', foreign_keys='ServerRequest.user_id', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class ServerRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # User who made the request
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Server specifications
    server_name = db.Column(db.String(100), nullable=False)
    server_type = db.Column(db.String(50), nullable=False)  # web, database, application, etc.
    cpu_cores = db.Column(db.Integer, nullable=False)
    memory_gb = db.Column(db.Integer, nullable=False)
    storage_gb = db.Column(db.Integer, nullable=False)
    operating_system = db.Column(db.String(50), nullable=False)
    
    # Application details
    application_name = db.Column(db.String(100), nullable=False)
    application_type = db.Column(db.String(50), nullable=False)
    application_description = db.Column(db.Text)
    
    # Request details
    business_justification = db.Column(db.Text, nullable=False)
    estimated_usage = db.Column(db.String(50), nullable=False)  # low, medium, high
    
    # Status and workflow
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, deploying, deployed, failed
    priority = db.Column(db.String(10), default='medium')  # low, medium, high, urgent
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    deployed_at = db.Column(db.DateTime)
    
    # Admin fields
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    admin_notes = db.Column(db.Text)
    deployment_notes = db.Column(db.Text)
    
    # Deployment details (populated after approval)
    server_ip = db.Column(db.String(15))
    deployment_progress = db.Column(db.Integer, default=0)  # 0-100
    
    def get_status_badge_class(self):
        status_classes = {
            'pending': 'bg-warning',
            'approved': 'bg-success',
            'rejected': 'bg-danger',
            'deploying': 'bg-info',
            'deployed': 'bg-primary',
            'failed': 'bg-danger'
        }
        return status_classes.get(self.status, 'bg-secondary')
    
    def get_priority_badge_class(self):
        priority_classes = {
            'low': 'bg-secondary',
            'medium': 'bg-info',
            'high': 'bg-warning',
            'urgent': 'bg-danger'
        }
        return priority_classes.get(self.priority, 'bg-secondary')
    
    def __repr__(self):
        return f'<ServerRequest {self.request_id}>'

class HetznerServer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hetzner_id = db.Column(db.Integer, unique=True, nullable=False)  # Hetzner server ID
    name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # running, stopped, starting, etc.
    server_type = db.Column(db.String(50), nullable=False)  # cx11, cx21, etc.
    image = db.Column(db.String(100), nullable=False)  # ubuntu-20.04, etc.
    
    # Network information
    public_ip = db.Column(db.String(15))
    private_ip = db.Column(db.String(15))
    ipv6 = db.Column(db.String(39))
    
    # Location and datacenter
    datacenter = db.Column(db.String(50))
    location = db.Column(db.String(50))
    
    # Specifications
    cpu_cores = db.Column(db.Integer)
    memory_gb = db.Column(db.Float)
    disk_gb = db.Column(db.Integer)
    
    # Management
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_synced = db.Column(db.DateTime, default=datetime.utcnow)
    managed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Deployment status
    deployment_status = db.Column(db.String(20), default='none')  # none, pending, deploying, deployed, failed
    deployment_log = db.Column(db.Text)
    last_deployment = db.Column(db.DateTime)
    
    manager = db.relationship('User', backref='managed_servers')
    
    def get_status_badge_class(self):
        status_classes = {
            'running': 'bg-success',
            'stopped': 'bg-secondary',
            'starting': 'bg-warning',
            'stopping': 'bg-warning',
            'rebooting': 'bg-info',
            'rebuilding': 'bg-danger',
            'migrating': 'bg-info',
            'unknown': 'bg-dark'
        }
        return status_classes.get(self.status, 'bg-secondary')
    
    def get_deployment_status_badge_class(self):
        status_classes = {
            'none': 'bg-secondary',
            'pending': 'bg-warning',
            'deploying': 'bg-info',
            'deployed': 'bg-success',
            'failed': 'bg-danger'
        }
        return status_classes.get(self.deployment_status, 'bg-secondary')
    
    def __repr__(self):
        return f'<HetznerServer {self.name}>'

class DeploymentScript(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    ansible_playbook = db.Column(db.Text, nullable=False)  # YAML content
    variables = db.Column(db.Text)  # JSON string of variables
    
    # Metadata
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Usage tracking
    execution_count = db.Column(db.Integer, default=0)
    last_executed = db.Column(db.DateTime)
    
    creator = db.relationship('User', backref='deployment_scripts')
    
    def __repr__(self):
        return f'<DeploymentScript {self.name}>'

class DeploymentExecution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    execution_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Relationships
    server_id = db.Column(db.Integer, db.ForeignKey('hetzner_server.id'), nullable=False)
    script_id = db.Column(db.Integer, db.ForeignKey('deployment_script.id'), nullable=False)
    executed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Execution details
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Logs and output
    ansible_output = db.Column(db.Text)
    error_log = db.Column(db.Text)
    exit_code = db.Column(db.Integer)
    
    # Variables used in this execution
    execution_variables = db.Column(db.Text)  # JSON string
    
    server = db.relationship('HetznerServer', backref='deployments')
    script = db.relationship('DeploymentScript', backref='executions')
    executor = db.relationship('User', backref='executed_deployments')
    
    def get_status_badge_class(self):
        status_classes = {
            'pending': 'bg-warning',
            'running': 'bg-info',
            'completed': 'bg-success',
            'failed': 'bg-danger'
        }
        return status_classes.get(self.status, 'bg-secondary')
    
    def __repr__(self):
        return f'<DeploymentExecution {self.execution_id}>'

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='info')  # info, success, warning, danger
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Optional link to related request
    request_id = db.Column(db.Integer, db.ForeignKey('server_request.id'))
    
    user = db.relationship('User', backref='notifications')
    request = db.relationship('ServerRequest', backref='notifications')
    
    def __repr__(self):
        return f'<Notification {self.title}>'
