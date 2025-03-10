"""empty message

Revision ID: afb2bc803903
Revises: 58ea09635556
Create Date: 2025-03-06 01:41:22.762066

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'afb2bc803903'
down_revision = '58ea09635556'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('amenities', schema=None) as batch_op:
        batch_op.add_column(sa.Column('icon', sa.String(length=50), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('amenities', schema=None) as batch_op:
        batch_op.drop_column('icon')

    # ### end Alembic commands ###
