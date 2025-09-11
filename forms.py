from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, IntegerField, DecimalField, TextAreaField, SubmitField
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

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), 
        Length(min=3, max=64)
    ])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    current_password = PasswordField('Current Password', validators=[DataRequired()], 
                                   description='Enter your current password to confirm changes')
    new_password = PasswordField('New Password (Optional)', validators=[
        Length(min=6, message='New password must be at least 6 characters long')
    ], description='Leave blank to keep current password')
    confirm_password = PasswordField('Confirm New Password', validators=[
        EqualTo('new_password', message='Passwords must match')
    ])
    submit = SubmitField('Update Profile')
    
    def __init__(self, original_user, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_user = original_user
    
    def validate_username(self, username):
        if username.data != self.original_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        if email.data != self.original_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email already registered. Please choose a different one.')
    
    def validate_current_password(self, current_password):
        from werkzeug.security import check_password_hash
        if not check_password_hash(self.original_user.password_hash, current_password.data):
            raise ValidationError('Current password is incorrect.')

class ServerRequestForm(FlaskForm):
    # Client details
    client_name = StringField('Client Name', validators=[
        DataRequired(), 
        Length(min=2, max=100, message='Client name must be between 2 and 100 characters')
    ], description='The name of the client this server is for (server name will be auto-generated)')
    
    # Project selection
    project_id = SelectField('Project', validators=[DataRequired()], coerce=int, 
                           description='Select which project this server should be created in')
    
    def validate_project_id(self, project_id):
        if project_id.data == 0:
            raise ValidationError('Please select a valid project.')
    
    # Subdomain (auto-suggested but editable)
    subdomain = StringField('Subdomain', validators=[
        DataRequired(), 
        Length(min=2, max=100, message='Subdomain must be between 2 and 100 characters')
    ], description='Subdomain for this server (auto-suggested from server name, editable)')
    
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

class SelfHostedServerForm(FlaskForm):
    # Basic server information
    name = StringField('Server Name', validators=[
        DataRequired(), 
        Length(min=2, max=100, message='Server name must be between 2 and 100 characters')
    ], description='A unique name for this self-hosted server')
    
    # Project selection
    project_id = SelectField('Project', validators=[DataRequired()], coerce=int, 
                           description='Select which project this server belongs to')
    
    # Client information
    client_name = StringField('Client Name', validators=[
        DataRequired(), 
        Length(min=2, max=100, message='Client name must be between 2 and 100 characters')
    ], description='The name of the client who owns this server')
    
    client_contact = StringField('Client Contact', validators=[
        Length(max=255, message='Contact information must be less than 255 characters')
    ], description='Client contact information (email, phone, etc.)')
    
    # Network information
    public_ip = StringField('Public IP Address', validators=[
        DataRequired(),
        Length(max=15)
    ], description='The public IP address of the server')
    
    private_ip = StringField('Private IP Address (Optional)', validators=[
        Length(max=15)
    ], description='Private/internal IP address if applicable')
    
    reverse_dns = StringField('Domain/Reverse DNS (Optional)', validators=[
        Length(max=255)
    ], description='Domain name or reverse DNS for this server')
    
    submit = SubmitField('Add Self-Hosted Server')
    
    def validate_project_id(self, project_id):
        if project_id.data == 0:
            raise ValidationError('Please select a valid project.')

class EditServerForm(FlaskForm):
    # Basic server information
    name = StringField('Server Name', validators=[
        DataRequired(), 
        Length(min=2, max=100, message='Server name must be between 2 and 100 characters')
    ], description='A unique name for this server')
    
    # Project selection (only for admins and managers)
    project_id = SelectField('Project', validators=[DataRequired()], coerce=int, 
                           description='Select which project this server belongs to')
    
    # Client information (only for client-managed servers)
    client_name = StringField('Client Name', validators=[
        Length(min=0, max=100, message='Client name must be less than 100 characters')
    ], description='The name of the client who owns this server')
    
    client_contact = StringField('Client Contact', validators=[
        Length(max=255, message='Contact information must be less than 255 characters')
    ], description='Client contact information (email, phone, etc.)')
    
    # Network information
    public_ip = StringField('Public IP Address', validators=[
        DataRequired(),
        Length(max=15)
    ], description='The public IP address of the server')
    
    private_ip = StringField('Private IP Address (Optional)', validators=[
        Length(max=15)
    ], description='Private/internal IP address if applicable')
    
    reverse_dns = StringField('Domain/Reverse DNS (Optional)', validators=[
        Length(max=255)
    ], description='Domain name or reverse DNS for this server')
    
    submit = SubmitField('Update Server')
    
    def validate_project_id(self, project_id):
        if project_id.data == 0:
            raise ValidationError('Please select a valid project.')

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
