import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
if not app.secret_key:
    raise RuntimeError("SESSION_SECRET environment variable must be set for security")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///server_provisioning.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Set maximum file upload size to 2GB to prevent memory/DoS issues
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024 * 1024

# initialize extensions
db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)
csrf.init_app(app)
login_manager.login_view = 'login'  # type: ignore
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

@app.context_processor
def inject_csrf_token():
    from flask_wtf.csrf import generate_csrf
    return dict(csrf_token=generate_csrf)

@app.context_processor
def inject_current_year():
    from datetime import datetime
    return dict(current_year=datetime.now().year)

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
    
    # Create Tokhy technical manager if he doesn't exist
    tokhy = models.User.query.filter_by(username='tokhy').first()
    if not tokhy:
        tokhy = models.User()
        tokhy.username = 'tokhy'
        tokhy.email = 'tokhy@company.com'
        tokhy.role = models.UserRole.TECHNICAL_AGENT
        tokhy.is_manager = True  # Manager level technical agent
        tokhy.set_password('tokhy123')
        db.session.add(tokhy)
        db.session.commit()
        logging.info("Created Tokhy technical manager: tokhy/tokhy123")

def create_sample_project_access():
    """Create sample project access permissions for demonstration"""
    import models
    # Get sample users and projects
    tech_agent = models.User.query.filter_by(username='tech_agent').first()
    sales_agent = models.User.query.filter_by(username='sales_agent').first()
    sohila = models.User.query.filter_by(username='sohila').first()
    tokhy = models.User.query.filter_by(username='tokhy').first()
    
    if not tech_agent or not sales_agent or not sohila or not tokhy:
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
        (tokhy.id, nova_project.id, 'admin'),       # Tokhy has admin access to Nova HR (though as manager he sees all anyway)
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
    
    # Assign existing servers to Nova HR project for Sohila
    assign_existing_servers_to_nova_hr(nova_project)
    
    db.session.commit()
    logging.info("Sample project access permissions created")

def assign_existing_servers_to_nova_hr(nova_project):
    """Assign 4 existing servers to Nova HR project for Sohila"""
    import models
    
    if not nova_project:
        return
    
    # Get first 4 existing servers that are in project 1 (default project)
    existing_servers = models.HetznerServer.query.filter_by(project_id=1).limit(4).all()
    
    # Assign them to Nova HR project
    for server in existing_servers:
        server.project_id = nova_project.id
    
    logging.info(f"Assigned {len(existing_servers)} existing servers to Nova HR project")

with app.app_context():
    # Import models to ensure tables are created
    import models
    db.create_all()
    
    # Add timezone conversion filter for templates
    import pytz
    
    def convert_to_cairo_timezone_filter(utc_datetime):
        """Convert UTC datetime to Cairo timezone for template usage"""
        if utc_datetime is None:
            return None
        
        utc_tz = pytz.UTC
        cairo_tz = pytz.timezone('Africa/Cairo')
        
        if utc_datetime.tzinfo is None:
            utc_datetime = utc_tz.localize(utc_datetime)
        
        return utc_datetime.astimezone(cairo_tz)
    
    app.jinja_env.filters['cairo_time'] = convert_to_cairo_timezone_filter
    
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

# Make UserRole available in all templates
from models import UserRole
@app.context_processor
def inject_user_role():
    return dict(UserRole=UserRole)

# Import routes
import routes
