"""Add unique constraint to ChatHistory

Revision ID: 3af58af0a128
Revises: bd3ebc183366
Create Date: 2024-05-20 14:00:05.750688

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3af58af0a128'
down_revision = 'bd3ebc183366'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('chat_history', schema=None) as batch_op:
        batch_op.create_unique_constraint('_session_content_uc', ['session_id', 'content'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('chat_history', schema=None) as batch_op:
        batch_op.drop_constraint('_session_content_uc', type_='unique')

    # ### end Alembic commands ###
