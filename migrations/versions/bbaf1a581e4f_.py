"""empty message

Revision ID: bbaf1a581e4f
Revises: a8a9ac9a005c
Create Date: 2019-11-26 16:57:06.368971

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bbaf1a581e4f'
down_revision = 'a8a9ac9a005c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('excerpts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('scores',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('wpm', sa.Float(), nullable=False),
    sa.Column('time', sa.Integer(), nullable=False),
    sa.Column('accuracy', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=200), nullable=False),
    sa.Column('username', sa.String(length=80), nullable=False),
    sa.Column('password', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('users')
    op.drop_table('scores')
    op.drop_table('excerpts')
    # ### end Alembic commands ###
