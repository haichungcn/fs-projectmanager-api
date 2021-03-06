"""empty message

Revision ID: 5d93e6a391d9
Revises: 45a87ec5be5c
Create Date: 2019-12-10 12:41:15.053879

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5d93e6a391d9'
down_revision = '45a87ec5be5c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('projects', sa.Column('status', sa.String(), nullable=True))
    op.add_column('teams', sa.Column('status', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('teams', 'status')
    op.drop_column('projects', 'status')
    # ### end Alembic commands ###
