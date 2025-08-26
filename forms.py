from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, IntegerField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, NumberRange, EqualTo, ValidationError
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), 
        Length(min=3, max=64)
    ])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[
        DataRequired(), 
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    password2 = PasswordField('Repeat Password', validators=[
        DataRequired(), 
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please choose a different one.')

class ServerRequestForm(FlaskForm):
    # Server details
    server_name = StringField('Server Name', validators=[
        DataRequired(), 
        Length(min=3, max=100, message='Server name must be between 3 and 100 characters')
    ])
    
    server_type = SelectField('Server Type', validators=[DataRequired()], choices=[
        ('web', 'Web Server'),
        ('database', 'Database Server'),
        ('application', 'Application Server'),
        ('cache', 'Cache Server'),
        ('file', 'File Server'),
        ('backup', 'Backup Server'),
        ('development', 'Development Server'),
        ('testing', 'Testing Server')
    ])
    
    # Hardware specifications
    cpu_cores = SelectField('CPU Cores', validators=[DataRequired()], coerce=int, choices=[
        (1, '1 Core'),
        (2, '2 Cores'),
        (4, '4 Cores'),
        (8, '8 Cores'),
        (16, '16 Cores'),
        (32, '32 Cores')
    ])
    
    memory_gb = SelectField('Memory (GB)', validators=[DataRequired()], coerce=int, choices=[
        (1, '1 GB'),
        (2, '2 GB'),
        (4, '4 GB'),
        (8, '8 GB'),
        (16, '16 GB'),
        (32, '32 GB'),
        (64, '64 GB'),
        (128, '128 GB')
    ])
    
    storage_gb = SelectField('Storage (GB)', validators=[DataRequired()], coerce=int, choices=[
        (20, '20 GB'),
        (50, '50 GB'),
        (100, '100 GB'),
        (250, '250 GB'),
        (500, '500 GB'),
        (1000, '1 TB'),
        (2000, '2 TB')
    ])
    
    operating_system = SelectField('Operating System', validators=[DataRequired()], choices=[
        ('ubuntu-20.04', 'Ubuntu 20.04 LTS'),
        ('ubuntu-22.04', 'Ubuntu 22.04 LTS'),
        ('centos-7', 'CentOS 7'),
        ('centos-8', 'CentOS 8'),
        ('rhel-8', 'Red Hat Enterprise Linux 8'),
        ('rhel-9', 'Red Hat Enterprise Linux 9'),
        ('windows-server-2019', 'Windows Server 2019'),
        ('windows-server-2022', 'Windows Server 2022')
    ])
    
    # Application details
    application_name = StringField('Application Name', validators=[
        DataRequired(), 
        Length(min=2, max=100, message='Application name must be between 2 and 100 characters')
    ])
    
    application_type = SelectField('Application Type', validators=[DataRequired()], choices=[
        ('web-app', 'Web Application'),
        ('api', 'API Service'),
        ('database', 'Database'),
        ('microservice', 'Microservice'),
        ('batch-job', 'Batch Processing'),
        ('analytics', 'Analytics/BI'),
        ('monitoring', 'Monitoring Tool'),
        ('ci-cd', 'CI/CD Pipeline'),
        ('other', 'Other')
    ])
    
    application_description = TextAreaField('Application Description', validators=[
        Length(max=500, message='Description cannot exceed 500 characters')
    ])
    
    # Business justification
    business_justification = TextAreaField('Business Justification', validators=[
        DataRequired(),
        Length(min=20, max=1000, message='Business justification must be between 20 and 1000 characters')
    ])
    
    estimated_usage = SelectField('Estimated Usage', validators=[DataRequired()], choices=[
        ('low', 'Low (< 100 users/day)'),
        ('medium', 'Medium (100-1000 users/day)'),
        ('high', 'High (1000-10000 users/day)'),
        ('very-high', 'Very High (> 10000 users/day)')
    ])
    
    priority = SelectField('Priority', validators=[DataRequired()], choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ])
    
    submit = SubmitField('Submit Request')

class AdminReviewForm(FlaskForm):
    status = SelectField('Status', validators=[DataRequired()], choices=[
        ('approved', 'Approve'),
        ('rejected', 'Reject')
    ])
    admin_notes = TextAreaField('Admin Notes', validators=[
        Length(max=1000, message='Notes cannot exceed 1000 characters')
    ])
    submit = SubmitField('Update Request')

class DeploymentScriptForm(FlaskForm):
    name = StringField('Script Name', validators=[
        DataRequired(), 
        Length(min=3, max=100, message='Script name must be between 3 and 100 characters')
    ])
    description = TextAreaField('Description', validators=[
        Length(max=500, message='Description cannot exceed 500 characters')
    ])
    ansible_playbook = TextAreaField('Ansible Playbook (YAML)', validators=[
        DataRequired(),
        Length(min=10, message='Playbook content is required')
    ])
    variables = TextAreaField('Variables (JSON)', validators=[
        Length(max=2000, message='Variables cannot exceed 2000 characters')
    ])
    submit = SubmitField('Save Script')

class ExecuteDeploymentForm(FlaskForm):
    script_id = SelectField('Deployment Script', validators=[DataRequired()], coerce=int)
    execution_variables = TextAreaField('Execution Variables (JSON)', validators=[
        Length(max=1000, message='Variables cannot exceed 1000 characters')
    ])
    submit = SubmitField('Execute Deployment')

class ServerManagementForm(FlaskForm):
    action = SelectField('Action', validators=[DataRequired()], choices=[
        ('start', 'Start Server'),
        ('stop', 'Stop Server'),
        ('reboot', 'Reboot Server')
    ])
    submit = SubmitField('Execute Action')
