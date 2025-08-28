# Server Provisioning System

## Overview

A Flask-based web application for managing server infrastructure requests with an automated approval workflow. The system enables users to submit detailed server provisioning requests, tracks them through approval stages, and provides real-time deployment monitoring. It features robust role-based access control with separate interfaces for regular users and administrators. The business vision is to streamline server management, reduce manual overhead, and provide a comprehensive platform for infrastructure provisioning and oversight.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### UI/UX Decisions
- **Template Engine**: Jinja2
- **UI Framework**: Bootstrap 5 with Font Awesome for responsive design
- **Theme**: Dark mode interface for professional use
- **JavaScript**: Vanilla JavaScript for dynamic features like form validation and live search

### Technical Implementations
- **Web Framework**: Flask with a modular structure
- **Authentication**: Flask-Login for session management and role-based access control (Technical Agents, Sales Agents, Administrators)
- **Form Handling**: WTForms for server-side validation and CSRF protection
- **Database ORM**: SQLAlchemy with declarative base model
- **Security**: Werkzeug for password hashing and proxy fix middleware
- **Deployment Automation**: Integration with Ansible for executing deployment scripts via SSH
- **Cloud Integration**: Hetzner Cloud API for server management and synchronization

### Feature Specifications
- **Request Workflow**: Multi-stage approval process (pending → approved → deployed)
- **Role-Specific Dashboards**: Customized interfaces for each user type with relevant features and statistics.
- **Permission System**: Granular permission checking based on user roles and project access.
- **Subscription Management**: Tracks client hosting dates, costs, and renewal automation.
- **Server Operations**: Initiates backups, system updates, and server monitoring.
- **Deployment Management**: Create, edit, and execute custom Ansible playbooks; track execution status and logs.
- **Project Organization**: Servers are organized into Hetzner Projects, each with independent SSH configurations and API tokens.
- **User Assignment System**: Admins and technical managers can assign specific technical agents to projects and individual servers with defined access levels (read, write, admin).
- **User Approval Workflow**: New user registrations require administrative approval before system access.

### System Design Choices
- **Database**: SQLite for development, PostgreSQL for production.
- **Data Models**: Comprehensive models for users, server requests, notifications, Hetzner servers, deployment scripts, execution tracking, client subscriptions, database backups, and system updates.
- **Connection Management**: SQLAlchemy engine with connection pooling and health checks.
- **Environment Configuration**: Utilizes environment variables for sensitive data like API tokens and database URLs.

## External Dependencies

- **Flask**: Main web framework.
- **Flask-SQLAlchemy**: ORM integration.
- **Flask-Login**: User authentication.
- **Flask-WTF**: Form handling.
- **WTForms**: Form validation.
- **hcloud**: Hetzner Cloud API client.
- **requests**: HTTP library.
- **ansible**: Infrastructure automation.
- **ansible-core**: Core Ansible functionality.
- **Bootstrap 5**: Frontend UI framework (via CDN).
- **Font Awesome 6**: Icon library.
- **Werkzeug**: WSGI utilities and security.
- **PostgreSQL**: Production database.

## Docker Deployment

The system now includes comprehensive Docker support for containerized deployment:

### Docker Configuration
- **Dockerfile**: Multi-stage Python 3.11 slim-based container with SSH client support
- **docker-compose.yml**: Production deployment with PostgreSQL database
- **docker-compose.override.yml**: Development configuration with live reload
- **Health Checks**: Automated health monitoring for web and database services
- **Volume Management**: Persistent PostgreSQL data and SSH key mounting
- **Environment Configuration**: Comprehensive .env support for secrets and configuration

### Deployment Options
- **Production**: `docker-compose up -d` for production deployment
- **Development**: Combined compose files for development with live reload
- **SSH Integration**: Automatic mounting of SSH keys for server management
- **Database Management**: Built-in PostgreSQL with backup and restore capabilities

### Added Files
- `Dockerfile`: Container definition with UV package manager
- `docker-compose.yml`: Multi-service orchestration
- `docker-compose.override.yml`: Development overrides
- `.dockerignore`: Optimized build context
- `.env.example`: Environment variable template
- `README-Docker.md`: Comprehensive deployment guide
- `docker-test.sh`: Automated testing and validation script

Date: August 28, 2025