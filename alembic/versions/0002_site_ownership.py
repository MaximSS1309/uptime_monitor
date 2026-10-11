"""site ownership: owner_id NOT NULL, url unique per owner

Revision ID: 0002_site_ownership
Revises: 0001_initial
Create Date: 2026-10-10 00:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0002_site_ownership"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DELETE FROM sites WHERE owner_id IS NULL")
    op.alter_column("sites", "owner_id", existing_type=sa.Integer(), nullable=False)

    op.drop_constraint("sites_url_key", "sites", type_="unique")
    op.create_unique_constraint("uq_sites_owner_url", "sites", ["owner_id", "url"])


def downgrade() -> None:
    op.drop_constraint("uq_sites_owner_url", "sites", type_="unique")
    op.create_unique_constraint("sites_url_key", "sites", ["url"])
    op.alter_column("sites", "owner_id", existing_type=sa.Integer(), nullable=True)