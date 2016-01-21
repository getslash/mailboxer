"""initial

Revision ID: 60381cf94c20
Revises: None
Create Date: 2016-01-21 23:17:16.850389

"""

# revision identifiers, used by Alembic.
revision = '60381cf94c20'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('mailbox',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('address', sa.String(length=160), nullable=True),
    sa.Column('last_activity', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mailbox_address'), 'mailbox', ['address'], unique=True)
    op.create_index(op.f('ix_mailbox_last_activity'), 'mailbox', ['last_activity'], unique=False)
    op.create_table('role',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=True),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('password', sa.String(length=255), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('confirmed_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('email',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('mailbox_id', sa.Integer(), nullable=True),
    sa.Column('fromaddr', sa.String(length=160), nullable=True),
    sa.Column('message', sa.Text(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('sent_via_ssl', sa.Boolean(), nullable=True),
    sa.Column('read', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['mailbox_id'], ['mailbox.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_mailbox_id'), 'email', ['mailbox_id'], unique=False)
    op.create_index(op.f('ix_email_timestamp'), 'email', ['timestamp'], unique=False)
    op.create_table('roles_users',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['role.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('roles_users')
    op.drop_index(op.f('ix_email_timestamp'), table_name='email')
    op.drop_index(op.f('ix_email_mailbox_id'), table_name='email')
    op.drop_table('email')
    op.drop_table('user')
    op.drop_table('role')
    op.drop_index(op.f('ix_mailbox_last_activity'), table_name='mailbox')
    op.drop_index(op.f('ix_mailbox_address'), table_name='mailbox')
    op.drop_table('mailbox')
    ### end Alembic commands ###
