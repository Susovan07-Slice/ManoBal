"""create_welfare_requests_table

Revision ID: b912c3f4e5a6
Revises: a844f6a8b55f
Create Date: 2026-09-25 23:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b912c3f4e5a6'
down_revision: Union[str, Sequence[str], None] = 'a844f6a8b55f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'welfare_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('personnel_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('urgency', sa.String(length=16), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['personnel_id'], ['personnel.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_welfare_requests_id'), 'welfare_requests', ['id'], unique=False)
    op.create_index(op.f('ix_welfare_requests_personnel_id'), 'welfare_requests', ['personnel_id'], unique=False)
    op.create_index(op.f('ix_welfare_requests_status'), 'welfare_requests', ['status'], unique=False)
    op.create_index(op.f('ix_welfare_requests_urgency'), 'welfare_requests', ['urgency'], unique=False)
    op.create_index(op.f('ix_welfare_requests_created_at'), 'welfare_requests', ['created_at'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_welfare_requests_created_at'), table_name='welfare_requests')
    op.drop_index(op.f('ix_welfare_requests_urgency'), table_name='welfare_requests')
    op.drop_index(op.f('ix_welfare_requests_status'), table_name='welfare_requests')
    op.drop_index(op.f('ix_welfare_requests_personnel_id'), table_name='welfare_requests')
    op.drop_index(op.f('ix_welfare_requests_id'), table_name='welfare_requests')
    op.drop_table('welfare_requests')
