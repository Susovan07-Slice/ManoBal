"""alter_risk_score_to_float

Revision ID: d134e5f6a7b8
Revises: c023d4e5f6a7
Create Date: 2026-09-26 13:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd134e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'c023d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.alter_column(
        'stress_assessments',
        'risk_score',
        existing_type=sa.Integer(),
        type_=sa.Float(),
        existing_nullable=False
    )

def downgrade() -> None:
    op.alter_column(
        'stress_assessments',
        'risk_score',
        existing_type=sa.Float(),
        type_=sa.Integer(),
        existing_nullable=False
    )
