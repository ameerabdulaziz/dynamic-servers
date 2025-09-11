"""Remove nova-hr-mail server

Revision ID: 001
Revises: 
Create Date: 2025-09-11 18:14:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Remove nova-hr-mail server and its related records"""
    # Remove user access records for nova-hr-mail server (ID 10)
    op.execute("DELETE FROM user_server_access WHERE server_id = 10")
    
    # Remove the nova-hr-mail server record
    op.execute("DELETE FROM hetzner_server WHERE name = 'nova-hr-mail' AND id = 10")


def downgrade():
    """This downgrade would require recreating the deleted server data which is not feasible"""
    pass