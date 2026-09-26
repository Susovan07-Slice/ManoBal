"""add_battalion_and_location_to_welfare_requests

Revision ID: e245f6a7b8c9
Revises: d134e5f6a7b8
Create Date: 2026-09-26 17:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e245f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'd134e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Add battalion and location columns to welfare_requests
    op.add_column(
        'welfare_requests',
        sa.Column('battalion', sa.String(length=64), nullable=True)
    )
    op.add_column(
        'welfare_requests',
        sa.Column('location', sa.String(length=64), nullable=True)
    )
    op.create_index(op.f('ix_welfare_requests_battalion'), 'welfare_requests', ['battalion'], unique=False)
    op.create_index(op.f('ix_welfare_requests_location'), 'welfare_requests', ['location'], unique=False)

    # 2. Backfill existing records from joined personnel record
    op.execute(
        """
        UPDATE welfare_requests
        SET battalion = personnel.battalion,
            location = personnel.location
        FROM personnel
        WHERE welfare_requests.personnel_id = personnel.id
          AND welfare_requests.battalion IS NULL
        """
    )

def downgrade() -> None:
    op.drop_index(op.f('ix_welfare_requests_location'), table_name='welfare_requests')
    op.drop_index(op.f('ix_welfare_requests_battalion'), table_name='welfare_requests')
    op.drop_column('welfare_requests', 'location')
    op.drop_column('welfare_requests', 'battalion')
