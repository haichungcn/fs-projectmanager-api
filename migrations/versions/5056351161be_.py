"""empty message

Revision ID: 5056351161be
Revises: da6b5129c018
Create Date: 2019-12-09 01:06:16.550998

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5056351161be'
down_revision = 'da6b5129c018'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('boards', sa.Column('status', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('boards', 'status')
    # ### end Alembic commands ###
