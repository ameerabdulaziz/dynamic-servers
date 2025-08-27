# Server Provisioning System

## Overview

A Flask-based web application for managing server infrastructure requests with an automated approval workflow. The system allows users to submit detailed server provisioning requests, tracks them through approval stages, and provides real-time deployment monitoring. It features role-based access control with separate interfaces for regular users and administrators.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Bootstrap 5 dark theme
- **UI Framework**: Bootstrap 5 with Font Awesome icons for responsive design
- **JavaScript**: Vanilla JavaScript for form validation, live search, and real-time updates
- **Theme**: Dark mode interface optimized for professional use

### Backend Architecture
- **Web Framework**: Flask with modular structure separating concerns
- **Authentication**: Flask-Login for session management with role-based access control
- **Form Handling**: WTForms for server-side validation and CSRF protection
- **Database ORM**: SQLAlchemy with declarative base model
- **Security**: Werkzeug password hashing and proxy fix middleware

### Data Storage
- **Database**: SQLite for development with PostgreSQL support via environment variables
- **Connection Pooling**: SQLAlchemy engine with connection recycling and health checks
- **Models**: User management, server requests, notification systems, Hetzner servers, deployment scripts, and execution tracking
- **Relationships**: Foreign key relationships between users, server requests, managed servers, and deployment executions
- **Extended Models**: HetznerServer, DeploymentScript, DeploymentExecution, HetznerProject for infrastructure management and project organization

### Authentication & Authorization
- **Three-Tier Role System**: Technical Agents, Sales Agents, and Administrators with distinct permissions
- **Role-Based Dashboards**: Customized interfaces for each user type with relevant features and statistics
- **Permission Checking**: Granular permission system controlling access to specific features and operations
- **Session Security**: Secure session management with configurable secret keys
- **Password Security**: Werkzeug password hashing with salt
- **Dynamic Navigation**: Menu items and features shown based on user role and permissions

### Application Features
- **Request Workflow**: Multi-stage approval process (pending → approved → deployed)
- **Role-Specific Features**:
  - **Technical Agents**: Server operations, backup management, system updates, deployment monitoring
  - **Sales Agents**: Server requests, subscription management, client revenue tracking
  - **Administrators**: Full system oversight, user management, approval workflows
- **Subscription Management**: Client hosting date management, cost tracking, renewal automation
- **Server Operations**: Backup initiation, system updates, server monitoring and control
- **Real-time Updates**: Progress tracking for server deployment with status updates
- **Form Validation**: Comprehensive client and server-side validation
- **Hetzner Cloud Integration**: Sync and manage existing servers from Hetzner Cloud provider
- **Ansible Deployment**: Execute deployment scripts using Ansible playbooks on managed servers
- **Deployment Scripts**: Create, edit, and execute custom Ansible playbooks with variables
- **Sample Scripts**: Pre-built deployment scripts for common tasks (Nginx, Docker, system updates)

## External Dependencies

### Core Framework Dependencies
- **Flask**: Web application framework
- **Flask-SQLAlchemy**: Database ORM integration
- **Flask-Login**: User authentication and session management
- **Flask-WTF**: Form handling and CSRF protection
- **WTForms**: Form validation and rendering

### Cloud Provider Integration
- **hcloud**: Hetzner Cloud API client for server management
- **requests**: HTTP library for API communications
- **ansible**: Infrastructure automation for deployment scripts
- **ansible-core**: Core Ansible functionality for playbook execution

### Infrastructure Management
- **Hetzner Cloud API**: Integration for listing, managing, and controlling cloud servers
- **Ansible Automation**: Execute deployment playbooks on remote servers
- **SSH Key Management**: Secure connections to managed servers
- **Deployment Tracking**: Monitor execution status and logs of deployment scripts

### Frontend Dependencies
- **Bootstrap 5**: UI framework loaded via CDN
- **Font Awesome 6**: Icon library for enhanced UI
- **Custom CSS**: Application-specific styling

### Development Tools
- **Werkzeug**: WSGI utilities and development server
- **SQLAlchemy**: Database toolkit and ORM

### Database Configuration
- **SQLite**: Default development database
- **PostgreSQL**: Production database support via DATABASE_URL environment variable
- **Connection Management**: Automatic connection pooling and health monitoring

### Security Libraries
- **Werkzeug Security**: Password hashing and security utilities
- **Flask-WTF CSRF**: Cross-site request forgery protection

### External Service Integration
- **Environment Variables**: Configuration via SESSION_SECRET, DATABASE_URL, and HETZNER_API_TOKEN
- **API Security**: Secure storage and handling of cloud provider API tokens
- **SSH Security**: Ansible connections using SSH key authentication

### Deployment Considerations
- **ProxyFix**: Werkzeug middleware for reverse proxy compatibility
- **Cloud Provider Access**: Integration with Hetzner Cloud for server management
- **Ansible Execution**: Secure playbook execution with variable injection
- **Logging**: Built-in Python logging configured for debugging and deployment tracking

### Recent Changes (August 27, 2025)
- **Project-Based Permissions System**: Fully implemented granular access control for technical agents
  - **UserProjectAccess Model**: New database model managing user access to specific projects with read/write/admin levels
  - **Access Hierarchy**: Read < Write < Admin permissions with proper validation
  - **Manager Override**: Technical agents with is_manager=True can access all projects like admins
  - **Server Filtering**: Technical agents only see servers from projects they have explicit access to
  - **Admin Interface**: Project Access management page for admins to grant/revoke user access
  - **Navigation Integration**: Added Project Access link to admin dropdown menu
- **Created Sohila Technical User**: New sample user for testing project-based permissions
  - **Username**: sohila (password: sohila123)
  - **Role**: Technical Agent (non-manager)
  - **Project Access**: Write access to Nova HR project only
  - **Server Count**: Can manage 4 Nova HR servers (web, api, database, backup)
- **Nova HR Project Sample Servers**: Added 4 dedicated servers for demonstration
  - **nova-hr-web-01**: cx21 server for web interface (168.119.249.64)
  - **nova-hr-api-01**: cx31 server for API backend (168.119.249.65)
  - **nova-hr-db-01**: cx41 server for database (168.119.249.66)
  - **nova-hr-backup-01**: cx21 server for backups (168.119.249.67)
- **Fixed Database Schema Issues**: Resolved hetzner_id field type compatibility with PostgreSQL
- **Project-Level SSH Configuration**: Moved SSH settings from individual servers to project-wide configuration for operational efficiency
  - **SSH Settings**: Each Hetzner project now has its own SSH credentials (username, port, private key, passphrase)
  - **Unified Access**: All servers in a project share the same SSH configuration
  - **Connection Testing**: SSH connection verification at project level with status indicators
  - **Remote Execution**: Both deployment and backup operations use project SSH settings
  - **Database Migration**: Added SSH fields to hetzner_projects table successfully
- **SSH-Based Remote Script Execution**: Fully functional remote server management via SSH
  - **Deployment Command**: `cd /home/dynamic/nova-hr-docker && ./deploy.sh`
  - **Backup Command**: `cd /home/dynamic/nova-hr-docker && docker compose exec backup ./usr/src/app/backup-db.sh`
  - **Error Handling**: Comprehensive logging and status tracking for all operations
  - **Security**: Encrypted SSH key storage and secure connection handling
- **Fixed Critical Backup Action Bug**: Resolved JavaScript form submission issue that prevented backup operations
  - **Root Cause**: JavaScript backup functions were showing alerts instead of submitting forms to backend
  - **Solution**: Updated frontend JavaScript to properly create and submit forms with CSRF tokens
  - **Database Models**: Added missing backup_log and error_log fields to DatabaseBackup model
  - **Verification**: All 15 servers now successfully execute backup operations via SSH
  - **Status**: Backup system fully operational with proper logging and error handling
- **Simplified Branding to "Dynamic Servers"**: Removed "Business" from branding for cleaner, more concise name
- **Implemented Three-Tier Role-Based Permission System**: 
  - **Technical Agents**: Server management, system updates, database backups, deployment operations
  - **Sales Agents**: Server requests, client subscription management, revenue tracking
  - **Administrators**: Full system access including user management and approval workflows
- **Enhanced Database Models**: Added ClientSubscription, DatabaseBackup, and SystemUpdate models for comprehensive tracking
- **Role-Specific Dashboards**: Separate dashboard interfaces tailored to each user role's responsibilities
- **Permission-Based Navigation**: Dynamic navigation menu showing only features accessible to user's role
- **PostgreSQL Integration**: Migrated to PostgreSQL with proper enum types for user roles
- **Sample User Creation**: Automatic creation of admin, technical agent, and sales agent demo accounts
- **Subscription Management**: Sales agents can manage client hosting dates, costs, and renewal settings
- **Server Operations Tracking**: Technical agents can initiate and monitor backups, updates, and system operations
- **Hetzner Projects Integration**: Added project-based organization with individual API tokens for each Hetzner Cloud project
- **Multi-Project Support**: Three initial projects created (Nova HR, Frappe ERP, Django Projects) with individual server management
- **Project-Based Server Organization**: Servers now organized by project with budget tracking and usage monitoring

### Previous Changes (August 26, 2025)
- **Added Hetzner Cloud Integration**: Full server listing, management, and monitoring
- **Implemented Ansible Service**: Deployment script execution with playbook validation
- **Extended Database Models**: New models for server management and deployment tracking
- **Enhanced Admin Interface**: Added server management sections to admin navigation
- **Created Sample Scripts**: Pre-built Ansible playbooks for common deployment tasks