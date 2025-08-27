import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///server_provisioning.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'  # type: ignore
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

def create_sohila_user():
    """Create Sohila technical user"""
    import models
    
    # Create Sohila if she doesn't exist
    sohila = models.User.query.filter_by(username='sohila').first()
    if not sohila:
        sohila = models.User()
        sohila.username = 'sohila'
        sohila.email = 'sohila@company.com'
        sohila.role = models.UserRole.TECHNICAL_AGENT
        sohila.is_manager = False
        sohila.set_password('sohila123')
        db.session.add(sohila)
        db.session.commit()
        logging.info("Created Sohila technical user: sohila/sohila123")

def create_sample_project_access():
    """Create sample project access permissions for demonstration"""
    import models
    # Get sample users and projects
    tech_agent = models.User.query.filter_by(username='tech_agent').first()
    sales_agent = models.User.query.filter_by(username='sales_agent').first()
    sohila = models.User.query.filter_by(username='sohila').first()
    
    if not tech_agent or not sales_agent or not sohila:
        return
    
    nova_project = models.HetznerProject.query.filter_by(name='Nova HR').first()
    frappe_project = models.HetznerProject.query.filter_by(name='Frappe ERP').first()
    
    if not nova_project or not frappe_project:
        return
    
    # Grant project access if it doesn't already exist
    access_grants = [
        (tech_agent.id, nova_project.id, 'write'),  # Tech agent has write access to Nova HR
        (tech_agent.id, frappe_project.id, 'read'), # Tech agent has read access to Frappe ERP
        (sales_agent.id, nova_project.id, 'read'),  # Sales agent has read access to Nova HR
        (sohila.id, nova_project.id, 'write'),      # Sohila has write access to Nova HR
    ]
    
    for user_id, project_id, access_level in access_grants:
        existing = models.UserProjectAccess.query.filter_by(user_id=user_id, project_id=project_id).first()
        if not existing:
            access = models.UserProjectAccess()
            access.user_id = user_id
            access.project_id = project_id
            access.access_level = access_level
            access.granted_by = 1  # Admin user ID
            db.session.add(access)
    
    # Create 4 sample servers for Nova HR project if they don't exist
    create_nova_hr_servers(nova_project)
    
    db.session.commit()
    logging.info("Sample project access permissions created")

def create_nova_hr_servers(nova_project):
    """Create 4 sample servers for Nova HR project"""
    import models
    
    if not nova_project:
        return
    
    # Define 4 sample servers for Nova HR
    server_data = [
        {
            'name': 'nova-hr-web-01',
            'hetzner_id': 50001,
            'server_type': 'cx21',
            'image': 'ubuntu-22.04',
            'public_ip': '168.119.249.64',
            'private_ip': '10.0.0.10',
            'status': 'running',
            'location': 'nbg1'
        },
        {
            'name': 'nova-hr-api-01',
            'hetzner_id': 50002,
            'server_type': 'cx31',
            'image': 'ubuntu-22.04',
            'public_ip': '168.119.249.65',
            'private_ip': '10.0.0.11',
            'status': 'running',
            'location': 'nbg1'
        },
        {
            'name': 'nova-hr-db-01',
            'hetzner_id': 50003,
            'server_type': 'cx41',
            'image': 'ubuntu-22.04',
            'public_ip': '168.119.249.66',
            'private_ip': '10.0.0.12',
            'status': 'running',
            'location': 'nbg1'
        },
        {
            'name': 'nova-hr-backup-01',
            'hetzner_id': 50004,
            'server_type': 'cx21',
            'image': 'ubuntu-22.04',
            'public_ip': '168.119.249.67',
            'private_ip': '10.0.0.13',
            'status': 'running',
            'location': 'nbg1'
        }
    ]
    
    for server_info in server_data:
        existing = models.HetznerServer.query.filter_by(hetzner_id=server_info['hetzner_id']).first()
        if not existing:
            server = models.HetznerServer()
            server.name = server_info['name']
            server.hetzner_id = server_info['hetzner_id']
            server.server_type = server_info['server_type']
            server.image = server_info['image']
            server.public_ip = server_info['public_ip']
            server.private_ip = server_info['private_ip']
            server.status = server_info['status']
            server.location = server_info['location']
            server.project_id = nova_project.id
            db.session.add(server)
    
    logging.info("Created 4 sample servers for Nova HR project")

with app.app_context():
    # Import models to ensure tables are created
    import models
    db.create_all()
    
    # Create admin user if it doesn't exist
    admin_user = models.User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = models.User(
            username='admin',
            email='admin@company.com',
            role=models.UserRole.ADMIN
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.commit()
        logging.info("Created admin user: admin/admin123")
    
    # Create sample technical agent if it doesn't exist
    tech_user = models.User.query.filter_by(username='tech_agent').first()
    if not tech_user:
        tech_user = models.User(
            username='tech_agent',
            email='tech@company.com',
            role=models.UserRole.TECHNICAL_AGENT
        )
        tech_user.set_password('tech123')
        db.session.add(tech_user)
        db.session.commit()
        logging.info("Created technical agent user: tech_agent/tech123")
    
    # Create sample sales agent if it doesn't exist
    sales_user = models.User.query.filter_by(username='sales_agent').first()
    if not sales_user:
        sales_user = models.User(
            username='sales_agent',
            email='sales@company.com',
            role=models.UserRole.SALES_AGENT
        )
        sales_user.set_password('sales123')
        db.session.add(sales_user)
        db.session.commit()
        logging.info("Created sales agent user: sales_agent/sales123")
    
    # Create default Hetzner projects if they don't exist
    projects_data = [
        {
            'name': 'Nova HR',
            'description': 'Human Resources management platform with employee onboarding, payroll, and performance tracking systems',
            'token': 'nova_hr_placeholder_token'
        },
        {
            'name': 'Frappe ERP',
            'description': 'Enterprise Resource Planning system with CRM, accounting, inventory, and project management modules',
            'token': 'frappe_erp_placeholder_token'
        },
        {
            'name': 'Django Projects',
            'description': 'Development and staging environment for Django-based web applications and API services',
            'token': 'django_projects_placeholder_token'
        }
    ]
    
    for project_data in projects_data:
        existing_project = models.HetznerProject.query.filter_by(name=project_data['name']).first()
        if not existing_project:
            project = models.HetznerProject(
                name=project_data['name'],
                description=project_data['description'],
                hetzner_api_token=project_data['token'],
                created_by=admin_user.id,
                max_servers=15,
                monthly_budget=500.00
            )
            db.session.add(project)
    
    db.session.commit()
    logging.info("Hetzner projects initialization completed")
    
    # Create Sohila technical user
    create_sohila_user()
    
    # Create sample project access permissions
    create_sample_project_access()
    
    logging.info("Application initialization completed")

# Import routes
import routes
