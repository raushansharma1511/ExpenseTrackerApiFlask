"""changes done

Revision ID: 164409804184
Revises: 3af1ba61cb68
Create Date: 2025-03-04 13:11:08.389654

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '164409804184'
down_revision = '3af1ba61cb68'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.drop_constraint('categories_user_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'users', ['user_id'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.drop_constraint('transactions_category_id_fkey', type_='foreignkey')
        batch_op.drop_constraint('transactions_user_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'users', ['user_id'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'categories', ['category_id'], ['id'], ondelete='CASCADE')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('transactions_user_id_fkey', 'users', ['user_id'], ['id'])
        batch_op.create_foreign_key('transactions_category_id_fkey', 'categories', ['category_id'], ['id'])

    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('categories_user_id_fkey', 'users', ['user_id'], ['id'])

    # ### end Alembic commands ###
