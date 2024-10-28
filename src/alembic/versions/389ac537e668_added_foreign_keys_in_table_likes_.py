"""Added foreign keys in table 'likes' relation 'users'

Revision ID: 389ac537e668
Revises: af19eb50a75c
Create Date: 2024-10-23 12:48:15.721481

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '389ac537e668'
down_revision: Union[str, None] = 'af19eb50a75c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key(None, 'subscribes', 'users', ['author_id'], ['id'])
    op.create_foreign_key(None, 'subscribes', 'users', ['follower_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'subscribes', type_='foreignkey')
    op.drop_constraint(None, 'subscribes', type_='foreignkey')
    # ### end Alembic commands ###