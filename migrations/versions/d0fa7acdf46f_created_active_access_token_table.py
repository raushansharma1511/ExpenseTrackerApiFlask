"""created Active access token table

Revision ID: d0fa7acdf46f
Revises: 1e46441610f8
Create Date: 2025-02-27 00:28:04.796214

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd0fa7acdf46f'
down_revision = '1e46441610f8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('active_access_tokens',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('access_token', sa.String(length=500), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('access_token')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('active_access_tokens')
    # ### end Alembic commands ###
