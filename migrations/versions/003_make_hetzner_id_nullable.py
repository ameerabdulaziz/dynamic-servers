"""Make hetzner_id nullable for self-hosted servers

Revision ID: 003
Revises: 002
Create Date: 2025-09-11 18:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """Make hetzner_id column nullable for self-hosted servers"""
    
    # Remove NOT NULL constraint from hetzner_id column
    try:
        op.alter_column('hetzner_server', 'hetzner_id',
                       existing_type=sa.Integer(),
                       nullable=True)
        print("✅ Made hetzner_id column nullable")
    except Exception as e:
        print(f"⚠️  Could not make hetzner_id nullable: {e}")


def downgrade():
    """Make hetzner_id NOT NULL again (dangerous - only if no self-hosted servers exist)"""
    
    # This is dangerous if self-hosted servers exist with NULL hetzner_id
    try:
        op.alter_column('hetzner_server', 'hetzner_id',
                       existing_type=sa.Integer(),
                       nullable=False)
        print("⚠️  Made hetzner_id NOT NULL again")
    except Exception as e:
        print(f"Could not make hetzner_id NOT NULL: {e}")