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
    # Client details
    client_name = StringField('Client Name', validators=[
        DataRequired(), 
        Length(min=2, max=100, message='Client name must be between 2 and 100 characters')
    ], description='The name of the client this server is for (server name will be auto-generated)')
    
    # Project selection
    project_id = SelectField('Project', validators=[DataRequired()], coerce=int, 
                           description='Select which project this server should be created in')
    
    # Business details (simplified)
    business_justification = TextAreaField('Business Justification', validators=[
        Length(max=1000, message='Business justification must be less than 1000 characters')
    ], description='Optional: Explain why this server is needed')
    
    estimated_usage = SelectField('Estimated Usage', validators=[DataRequired()], choices=[
        ('< 50', '< 50 users (1 Core, 2GB RAM, 20GB Storage)'),
        ('low', 'Low (2 Cores, 4GB RAM, 40GB Storage)'),
        ('medium', 'Medium (2 Cores, 8GB RAM, 80GB Storage)'),
        ('high', 'High (4 Cores, 16GB RAM, 160GB Storage)')
    ], description='Server specifications will be automatically assigned based on usage')
    
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
