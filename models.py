from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum
import uuid

class UserRole(Enum):
    ADMIN = "admin"
    TECHNICAL_AGENT = "technical_agent" 
    SALES_AGENT = "sales_agent"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.SALES_AGENT, nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with server requests - specify foreign_keys to avoid ambiguity
    requests = db.relationship('ServerRequest', foreign_keys='ServerRequest.user_id', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN
    
    @property
    def is_technical_agent(self):
        return self.role == UserRole.TECHNICAL_AGENT
    
    @property
    def is_sales_agent(self):
        return self.role == UserRole.SALES_AGENT
    
    @property
    def role_display(self):
        role_names = {
            UserRole.ADMIN: "Administrator",
            UserRole.TECHNICAL_AGENT: "Technical Agent",
            UserRole.SALES_AGENT: "Sales Agent"
        }
        return role_names.get(self.role, "Unknown")
    
    def has_permission(self, permission):
        """Check if user has specific permission based on role"""
        permissions = {
            UserRole.ADMIN: [
                'manage_users', 'manage_servers', 'approve_requests', 
                'view_all_requests', 'manage_deployments', 'system_admin',
                'manage_subscriptions', 'database_operations', 'server_operations'
            ],
            UserRole.TECHNICAL_AGENT: [
                'manage_servers', 'view_approved_servers', 'manage_deployments',
                'database_operations', 'system_updates', 'server_monitoring',
                'server_operations', 'backup_operations'
            ],
            UserRole.SALES_AGENT: [
                'create_requests', 'view_own_requests', 'view_approved_servers',
                'manage_subscriptions', 'client_management'
            ]
        }
        return permission in permissions.get(self.role, [])
    
    def __repr__(self):
        return f'<User {self.username} ({self.role_display})>'

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

# New models for enhanced role-based features

class ClientSubscription(db.Model):
    """Manages client hosting subscription dates and details"""
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100), nullable=False)
    client_email = db.Column(db.String(120), nullable=False)
    
    # Subscription details
    subscription_start = db.Column(db.Date, nullable=False)
    subscription_end = db.Column(db.Date, nullable=False)
    subscription_type = db.Column(db.String(50), nullable=False)  # basic, premium, enterprise
    monthly_cost = db.Column(db.Float, nullable=False)
    
    # Server association
    server_id = db.Column(db.Integer, db.ForeignKey('hetzner_server.id'))
    
    # Management tracking
    managed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Sales agent
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    auto_renewal = db.Column(db.Boolean, default=True)
    
    # Relationships
    server = db.relationship('HetznerServer', backref='subscriptions')
    manager = db.relationship('User', backref='managed_subscriptions')
    
    @property
    def days_remaining(self):
        from datetime import date
        return (self.subscription_end - date.today()).days
    
    @property
    def is_expiring_soon(self):
        return self.days_remaining <= 30
    
    def __repr__(self):
        return f'<ClientSubscription {self.client_name}>'

class DatabaseBackup(db.Model):
    """Tracks database backup operations performed by technical agents"""
    id = db.Column(db.Integer, primary_key=True)
    backup_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Backup details
    server_id = db.Column(db.Integer, db.ForeignKey('hetzner_server.id'), nullable=False)
    database_name = db.Column(db.String(100), nullable=False)
    backup_type = db.Column(db.String(20), nullable=False)  # full, incremental, differential
    
    # Backup metadata
    backup_size = db.Column(db.BigInteger)  # Size in bytes
    backup_path = db.Column(db.String(255))  # Storage location
    compression_used = db.Column(db.Boolean, default=True)
    encryption_used = db.Column(db.Boolean, default=True)
    
    # Execution details
    started_at = db.Column(db.DateTime, nullable=False)
    completed_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='running')  # running, completed, failed, cancelled
    
    # User tracking
    initiated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Error handling
    error_message = db.Column(db.Text)
    retry_count = db.Column(db.Integer, default=0)
    
    # Relationships
    server = db.relationship('HetznerServer', backref='backups')
    operator = db.relationship('User', backref='backup_operations')
    
    @property
    def duration_minutes(self):
        if self.completed_at and self.started_at:
            return int((self.completed_at - self.started_at).total_seconds() / 60)
        return None
    
    @property
    def backup_size_mb(self):
        if self.backup_size:
            return round(self.backup_size / 1024 / 1024, 2)
        return None
    
    def get_status_badge_class(self):
        status_classes = {
            'running': 'bg-info',
            'completed': 'bg-success',
            'failed': 'bg-danger',
            'cancelled': 'bg-warning'
        }
        return status_classes.get(self.status, 'bg-secondary')
    
    def __repr__(self):
        return f'<DatabaseBackup {self.backup_id}>'

class SystemUpdate(db.Model):
    """Tracks system updates performed by technical agents"""
    id = db.Column(db.Integer, primary_key=True)
    update_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Update details
    server_id = db.Column(db.Integer, db.ForeignKey('hetzner_server.id'), nullable=False)
    update_type = db.Column(db.String(30), nullable=False)  # security, system, application, kernel
    update_description = db.Column(db.Text, nullable=False)
    
    # Package information
    packages_updated = db.Column(db.Text)  # JSON list of updated packages
    kernel_update = db.Column(db.Boolean, default=False)
    reboot_required = db.Column(db.Boolean, default=False)
    reboot_completed = db.Column(db.Boolean, default=False)
    
    # Execution details
    scheduled_at = db.Column(db.DateTime)
    started_at = db.Column(db.DateTime, nullable=False)
    completed_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='running')  # scheduled, running, completed, failed, rollback
    
    # User tracking
    initiated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Monitoring
    pre_update_snapshot = db.Column(db.String(255))  # Snapshot ID if taken
    rollback_available = db.Column(db.Boolean, default=False)
    rollback_completed = db.Column(db.Boolean, default=False)
    
    # Error handling
    error_message = db.Column(db.Text)
    rollback_reason = db.Column(db.Text)
    
    # Relationships
    server = db.relationship('HetznerServer', backref='system_updates')
    operator = db.relationship('User', foreign_keys=[initiated_by], backref='initiated_updates')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_updates')
    
    def get_status_badge_class(self):
        status_classes = {
            'scheduled': 'bg-info',
            'running': 'bg-warning',
            'completed': 'bg-success',
            'failed': 'bg-danger',
            'rollback': 'bg-warning'
        }
        return status_classes.get(self.status, 'bg-secondary')
    
    def __repr__(self):
        return f'<SystemUpdate {self.update_id}>'

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
