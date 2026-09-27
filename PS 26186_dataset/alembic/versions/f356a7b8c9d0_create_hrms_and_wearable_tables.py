"""create_hrms_and_wearable_tables

Revision ID: f356a7b8c9d0
Revises: e245f6a7b8c9
Create Date: 2026-09-26 20:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f356a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'e245f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create hrms_service_records table
    op.create_table(
        'hrms_service_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('personnel_id', sa.Integer(), nullable=False),
        sa.Column('service_number', sa.String(length=64), nullable=True),
        sa.Column('department', sa.String(length=64), nullable=True),
        sa.Column('battalion', sa.String(length=64), nullable=True),
        sa.Column('location', sa.String(length=64), nullable=True),
        sa.Column('job_role', sa.String(length=64), nullable=True),
        sa.Column('rank', sa.String(length=64), nullable=True),
        sa.Column('deployment_days', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('duty_hours_per_week', sa.Float(), nullable=True),
        sa.Column('night_shifts_per_month', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('consecutive_duty_days', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('leave_gap_days', sa.Integer(), nullable=True, server_default='30'),
        sa.Column('annual_leaves_taken', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('transfer_frequency', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('training_load', sa.Integer(), nullable=True, server_default='2'),
        sa.Column('experience_years', sa.Float(), nullable=True),
        sa.Column('source', sa.String(length=32), nullable=False, server_default='mock_hrms'),
        sa.Column('raw_metadata', sa.String(length=512), nullable=True),
        sa.Column('synced_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['personnel_id'], ['personnel.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_hrms_service_records_id'), 'hrms_service_records', ['id'], unique=False)
    op.create_index(op.f('ix_hrms_service_records_personnel_id'), 'hrms_service_records', ['personnel_id'], unique=True)
    op.create_index(op.f('ix_hrms_service_records_service_number'), 'hrms_service_records', ['service_number'], unique=False)
    op.create_index(op.f('ix_hrms_service_records_battalion'), 'hrms_service_records', ['battalion'], unique=False)
    op.create_index(op.f('ix_hrms_service_records_location'), 'hrms_service_records', ['location'], unique=False)

    # 2. Create wearable_telemetry table
    op.create_table(
        'wearable_telemetry',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('personnel_id', sa.Integer(), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('heart_rate', sa.Float(), nullable=True),
        sa.Column('hrv_rmssd', sa.Float(), nullable=True),
        sa.Column('sleep_duration_hours', sa.Float(), nullable=True),
        sa.Column('sleep_quality_score', sa.Float(), nullable=True),
        sa.Column('step_count', sa.Integer(), nullable=True),
        sa.Column('active_minutes', sa.Integer(), nullable=True),
        sa.Column('source', sa.String(length=32), nullable=False, server_default='simulated_wearable'),
        sa.Column('device_model', sa.String(length=64), nullable=True, server_default='Simulated Band v1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['personnel_id'], ['personnel.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_wearable_telemetry_id'), 'wearable_telemetry', ['id'], unique=False)
    op.create_index(op.f('ix_wearable_telemetry_personnel_id'), 'wearable_telemetry', ['personnel_id'], unique=False)
    op.create_index(op.f('ix_wearable_telemetry_recorded_at'), 'wearable_telemetry', ['recorded_at'], unique=False)
    op.create_index('ix_wearable_telemetry_personnel_recorded', 'wearable_telemetry', ['personnel_id', 'recorded_at'], unique=False)

def downgrade() -> None:
    op.drop_index('ix_wearable_telemetry_personnel_recorded', table_name='wearable_telemetry')
    op.drop_index(op.f('ix_wearable_telemetry_recorded_at'), table_name='wearable_telemetry')
    op.drop_index(op.f('ix_wearable_telemetry_personnel_id'), table_name='wearable_telemetry')
    op.drop_index(op.f('ix_wearable_telemetry_id'), table_name='wearable_telemetry')
    op.drop_table('wearable_telemetry')

    op.drop_index(op.f('ix_hrms_service_records_location'), table_name='hrms_service_records')
    op.drop_index(op.f('ix_hrms_service_records_battalion'), table_name='hrms_service_records')
    op.drop_index(op.f('ix_hrms_service_records_service_number'), table_name='hrms_service_records')
    op.drop_index(op.f('ix_hrms_service_records_personnel_id'), table_name='hrms_service_records')
    op.drop_index(op.f('ix_hrms_service_records_id'), table_name='hrms_service_records')
    op.drop_table('hrms_service_records')
