"""empty message

Revision ID: da6b5129c018
Revises: 26bb4b9f8a66
Create Date: 2019-12-06 16:56:35.604621

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'da6b5129c018'
down_revision = '26bb4b9f8a66'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tasks', sa.Column('assignee_id', sa.Integer(), nullable=True))
    op.drop_constraint('tasks_user_id_fkey', 'tasks', type_='foreignkey')
    op.create_foreign_key(None, 'tasks', 'users', ['assignee_id'], ['id'])
    op.drop_column('tasks', 'user_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tasks', sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'tasks', type_='foreignkey')
    op.create_foreign_key('tasks_user_id_fkey', 'tasks', 'users', ['user_id'], ['id'])
    op.drop_column('tasks', 'assignee_id')
    # ### end Alembic commands ###
