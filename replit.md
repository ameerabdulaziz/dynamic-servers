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
- **Models**: User management, server requests, and notification systems
- **Relationships**: Foreign key relationships between users and their server requests

### Authentication & Authorization
- **User Management**: Registration, login, and role-based permissions
- **Admin Controls**: Separate admin interface for request approval and system management
- **Session Security**: Secure session management with configurable secret keys
- **Password Security**: Werkzeug password hashing with salt

### Application Features
- **Request Workflow**: Multi-stage approval process (pending → approved → deployed)
- **Real-time Updates**: Progress tracking for server deployment with status updates
- **Dashboard**: User and admin dashboards with statistics and request management
- **Form Validation**: Comprehensive client and server-side validation

## External Dependencies

### Core Framework Dependencies
- **Flask**: Web application framework
- **Flask-SQLAlchemy**: Database ORM integration
- **Flask-Login**: User authentication and session management
- **Flask-WTF**: Form handling and CSRF protection
- **WTForms**: Form validation and rendering

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

### Deployment Considerations
- **ProxyFix**: Werkzeug middleware for reverse proxy compatibility
- **Environment Variables**: Configuration via SESSION_SECRET and DATABASE_URL
- **Logging**: Built-in Python logging configured for debugging