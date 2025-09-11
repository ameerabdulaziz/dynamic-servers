"""Add server_source and client fields to HetznerServer

Revision ID: 002
Revises: 001
Create Date: 2025-09-11 18:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    """Add missing columns to HetznerServer table"""
    
    # Add server_source column if it doesn't exist
    try:
        op.add_column('hetzner_server', sa.Column('server_source', sa.String(length=20), nullable=False, server_default='hetzner'))
    except Exception:
        # Column might already exist
        pass
    
    # Add client_name column if it doesn't exist
    try:
        op.add_column('hetzner_server', sa.Column('client_name', sa.String(length=100), nullable=True))
    except Exception:
        # Column might already exist
        pass
    
    # Add client_contact column if it doesn't exist
    try:
        op.add_column('hetzner_server', sa.Column('client_contact', sa.String(length=255), nullable=True))
    except Exception:
        # Column might already exist
        pass


def downgrade():
    """Remove the added columns"""
    try:
        op.drop_column('hetzner_server', 'client_contact')
    except Exception:
        pass
    
    try:
        op.drop_column('hetzner_server', 'client_name')
    except Exception:
        pass
    
    try:
        op.drop_column('hetzner_server', 'server_source')
    except Exception:
        pass