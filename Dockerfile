# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including SSH client for server management
RUN apt-get update && apt-get install -y \
    openssh-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY pyproject.toml uv.lock ./

# Install UV package manager and dependencies
RUN pip install uv
RUN uv sync --frozen

# Copy application code
COPY . .

# Create .ssh directory for SSH keys
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=main.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Run the application using gunicorn
CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "main:app"]