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

# Import routes
import routes
