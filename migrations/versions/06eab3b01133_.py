"""empty message

Revision ID: 06eab3b01133
Revises: 1d6f28b8addb
Create Date: 2019-12-05 18:47:25.075203

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '06eab3b01133'
down_revision = '1d6f28b8addb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tasks', sa.Column('note', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('tasks', 'note')
    # ### end Alembic commands ###
