"""initial schema

Revision ID: ea94b0fe976f
Revises:
Create Date: 2026-05-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ea94b0fe976f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=80), nullable=False),
        sa.Column('display_name', sa.String(length=80), nullable=True),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('password_hash', sa.String(length=256), nullable=False),
        sa.Column('bio', sa.String(length=160), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_index('ix_user_email', ['email'], unique=True)

    op.create_table('bot',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('style', sa.String(length=32), nullable=False),
        sa.Column('style_icon', sa.String(length=64), nullable=False),
        sa.Column('description', sa.String(length=256), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    op.create_table('post',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bot_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('source_url', sa.String(length=512), nullable=True),
        sa.Column('source_title', sa.String(length=300), nullable=True),
        sa.Column('source_hash', sa.String(length=64), nullable=False),
        sa.Column('votes', sa.Integer(), nullable=True),
        sa.Column('comments_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['bot_id'], ['bot.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.create_index('ix_post_source_hash', ['source_hash'], unique=True)

    op.create_table('vote',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('value', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['post_id'], ['post.id']),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('post_id', 'user_id', name='unique_user_post_vote'),
    )

    op.create_table('comment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['post_id'], ['post.id']),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('comment')
    op.drop_table('vote')
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.drop_index('ix_post_source_hash')
    op.drop_table('post')
    op.drop_table('bot')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_index('ix_user_email')
    op.drop_table('user')
