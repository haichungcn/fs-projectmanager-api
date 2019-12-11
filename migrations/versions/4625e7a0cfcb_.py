"""empty message

Revision ID: 4625e7a0cfcb
Revises: d5b5d7ca5236
Create Date: 2019-12-11 19:58:50.752919

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4625e7a0cfcb'
down_revision = 'd5b5d7ca5236'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('status', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'status')
    # ### end Alembic commands ###
