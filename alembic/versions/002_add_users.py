"""
alembic/versions/002_add_users.py
เพิ่ม table users สำหรับ Authentication
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '002_add_users'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id',              UUID(as_uuid=True),         primary_key=True),
        sa.Column('username',        sa.String(50),              nullable=False, unique=True),
        sa.Column('email',           sa.String(255),             nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255),             nullable=False),
        sa.Column('display_name',    sa.String(100),             nullable=True),
        sa.Column('gender',          sa.String(10),              nullable=True),
        sa.Column('is_active',       sa.Boolean(),               nullable=False, server_default='true'),
        sa.Column('created_at',      sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_login',      sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email',    'users', ['email'],    unique=True)

    # เพิ่ม owner_id ใน cats เชื่อมกับ users
    op.add_column('cats', sa.Column('owner_id', UUID(as_uuid=True),
                                    sa.ForeignKey('users.id', ondelete='CASCADE'),
                                    nullable=True))
    op.create_index('ix_cats_owner_id', 'cats', ['owner_id'])


def downgrade() -> None:
    op.drop_index('ix_cats_owner_id', 'cats')
    op.drop_column('cats', 'owner_id')
    op.drop_index('ix_users_email',    'users')
    op.drop_index('ix_users_username', 'users')
    op.drop_table('users')
