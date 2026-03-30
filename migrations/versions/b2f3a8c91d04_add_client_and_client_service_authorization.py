"""add client and client_service_authorization tables

Revision ID: b2f3a8c91d04
Revises: 40eb0c23e103
Create Date: 2026-03-30 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2f3a8c91d04"
down_revision: str | Sequence[str] | None = "40eb0c23e103"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "client",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("client_secret", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_client_id"), "client", ["id"], unique=False)
    op.create_index(op.f("ix_client_client_id"), "client", ["client_id"], unique=True)

    op.create_table(
        "client_service_authorization",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("client.id"), nullable=False),
        sa.Column("service", sa.String(), nullable=False),
        sa.Column("quotas", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("client_id", "service", name="uq_client_service"),
    )
    op.create_index(
        op.f("ix_client_service_authorization_id"),
        "client_service_authorization",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_client_service_authorization_id"), table_name="client_service_authorization")
    op.drop_table("client_service_authorization")
    op.drop_index(op.f("ix_client_client_id"), table_name="client")
    op.drop_index(op.f("ix_client_id"), table_name="client")
    op.drop_table("client")
