"""add_battalion_and_scope_fields

Revision ID: c023d4e5f6a7
Revises: b912c3f4e5a6
Create Date: 2026-09-26 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c023d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'b912c3f4e5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Add battalion to personnel with safe default '7th Battalion'
    op.add_column(
        'personnel',
        sa.Column('battalion', sa.String(length=64), nullable=False, server_default='7th Battalion')
    )
    op.create_index(op.f('ix_personnel_battalion'), 'personnel', ['battalion'], unique=False)

    # 2. Add battalion and location to users table for organizational scoping
    op.add_column(
        'users',
        sa.Column('battalion', sa.String(length=64), nullable=True)
    )
    op.add_column(
        'users',
        sa.Column('location', sa.String(length=64), nullable=True)
    )
    op.create_index(op.f('ix_users_battalion'), 'users', ['battalion'], unique=False)
    op.create_index(op.f('ix_users_location'), 'users', ['location'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_users_location'), table_name='users')
    op.drop_index(op.f('ix_users_battalion'), table_name='users')
    op.drop_column('users', 'location')
    op.drop_column('users', 'battalion')
    op.drop_index(op.f('ix_personnel_battalion'), table_name='personnel')
    op.drop_column('personnel', 'battalion')
