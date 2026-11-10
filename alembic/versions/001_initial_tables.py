"""initial tables

Revision ID: 001_initial
Revises: 
Create Date: 2026-07-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- cats ------------------------------------------------------------------
    op.create_table(
        'cats',
        sa.Column('id',                UUID(as_uuid=True),         primary_key=True),
        sa.Column('name',              sa.String(100),              nullable=False),
        sa.Column('breed',             sa.String(100),              nullable=True),
        sa.Column('gender',            sa.String(10),               nullable=False),
        sa.Column('birth_date',        sa.Date(),                   nullable=True),
        sa.Column('color',             sa.String(50),               nullable=True),
        sa.Column('profile_image_url', sa.Text(),                   nullable=True),
        sa.Column('is_active',         sa.Boolean(),                nullable=False, server_default='true'),
        sa.Column('created_at',        sa.DateTime(timezone=True),  nullable=False, server_default=sa.text('now()')),
    )

    # -- activities ------------------------------------------------------------
    op.create_table(
        'activities',
        sa.Column('id',            UUID(as_uuid=True),        primary_key=True),
        sa.Column('cat_id',        UUID(as_uuid=True),        sa.ForeignKey('cats.id', ondelete='CASCADE'), nullable=False),
        sa.Column('activity_type', sa.String(30),             nullable=False),
        sa.Column('recorded_at',   sa.DateTime(timezone=True),nullable=False),
        sa.Column('weight_kg',     sa.Float(),                nullable=True),
        sa.Column('food_brand',    sa.String(100),            nullable=True),
        sa.Column('food_type',     sa.String(20),             nullable=True),
        sa.Column('food_amount_g', sa.Float(),                nullable=True),
        sa.Column('litter_type',   sa.String(50),             nullable=True),
        sa.Column('notes',         sa.Text(),                 nullable=True),
        sa.Column('created_at',    sa.DateTime(timezone=True),nullable=False, server_default=sa.text('now()')),
    )

    # -- expenses --------------------------------------------------------------
    op.create_table(
        'expenses',
        sa.Column('id',                UUID(as_uuid=True),        primary_key=True),
        sa.Column('cat_id',            UUID(as_uuid=True),        sa.ForeignKey('cats.id', ondelete='SET NULL'), nullable=True),
        sa.Column('category',          sa.String(30),             nullable=False),
        sa.Column('amount',            sa.Numeric(10, 2),         nullable=False),
        sa.Column('description',       sa.String(255),            nullable=True),
        sa.Column('receipt_image_url', sa.Text(),                 nullable=True),
        sa.Column('expense_date',      sa.Date(),                 nullable=False),
        sa.Column('created_at',        sa.DateTime(timezone=True),nullable=False, server_default=sa.text('now()')),
    )

    # -- reminders -------------------------------------------------------------
    op.create_table(
        'reminders',
        sa.Column('id',                 UUID(as_uuid=True),        primary_key=True),
        sa.Column('cat_id',             UUID(as_uuid=True),        sa.ForeignKey('cats.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reminder_type',      sa.String(30),             nullable=False),
        sa.Column('title',              sa.String(200),            nullable=False),
        sa.Column('description',        sa.Text(),                 nullable=True),
        sa.Column('due_date',           sa.Date(),                 nullable=False),
        sa.Column('due_time',           sa.Time(),                 nullable=True),
        sa.Column('is_recurring',       sa.Boolean(),              nullable=False, server_default='false'),
        sa.Column('recurrence_days',    sa.Integer(),              nullable=True),
        sa.Column('notify_before_days', sa.Integer(),              nullable=False, server_default='3'),
        sa.Column('status',             sa.String(20),             nullable=False, server_default='pending'),
        sa.Column('notified_at',        sa.DateTime(timezone=True),nullable=True),
        sa.Column('created_at',         sa.DateTime(timezone=True),nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at',         sa.DateTime(timezone=True),nullable=False, server_default=sa.text('now()')),
    )

    # -- indexes ---------------------------------------------------------------
    op.create_index('ix_activities_cat_id',   'activities', ['cat_id'])
    op.create_index('ix_activities_recorded', 'activities', ['recorded_at'])
    op.create_index('ix_expenses_cat_id',     'expenses',   ['cat_id'])
    op.create_index('ix_expenses_date',       'expenses',   ['expense_date'])
    op.create_index('ix_reminders_cat_id',    'reminders',  ['cat_id'])
    op.create_index('ix_reminders_due_date',  'reminders',  ['due_date'])
    op.create_index('ix_reminders_status',    'reminders',  ['status'])


def downgrade() -> None:
    op.drop_index('ix_reminders_status',    'reminders')
    op.drop_index('ix_reminders_due_date',  'reminders')
    op.drop_index('ix_reminders_cat_id',    'reminders')
    op.drop_index('ix_expenses_date',       'expenses')
    op.drop_index('ix_expenses_cat_id',     'expenses')
    op.drop_index('ix_activities_recorded', 'activities')
    op.drop_index('ix_activities_cat_id',   'activities')
    op.drop_table('reminders')
    op.drop_table('expenses')
    op.drop_table('activities')
    op.drop_table('cats')
