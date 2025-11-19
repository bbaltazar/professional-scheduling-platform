"""add_workplace_id_to_calendar_events

Revision ID: 4976b5d06d1e
Revises: 77fb5ce9d2e1
Create Date: 2025-11-08 10:05:24.122025

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4976b5d06d1e"
down_revision: Union[str, Sequence[str], None] = "77fb5ce9d2e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add workplace_id column to calendar_events table."""
    # For SQLite, we use batch mode to add column with foreign key
    with op.batch_alter_table("calendar_events", schema=None) as batch_op:
        batch_op.add_column(sa.Column("workplace_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_calendar_events_workplace_id", "workplaces", ["workplace_id"], ["id"]
        )
        batch_op.create_index("ix_calendar_events_workplace_id", ["workplace_id"])


def downgrade() -> None:
    """Downgrade schema: Remove workplace_id column from calendar_events table."""
    # For SQLite, we use batch mode to drop column
    with op.batch_alter_table("calendar_events", schema=None) as batch_op:
        batch_op.drop_index("ix_calendar_events_workplace_id")
        batch_op.drop_constraint("fk_calendar_events_workplace_id", type_="foreignkey")
        batch_op.drop_column("workplace_id")
