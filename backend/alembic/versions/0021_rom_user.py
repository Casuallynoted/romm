"""empty message

Revision ID: 0021_rom_user
Revises: 0020_created_and_updated
Create Date: 2024-06-29 00:11:51.800988

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0021_rom_user"
down_revision = "0020_created_and_updated"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "rom_user",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("note_raw_markdown", sa.Text(), nullable=False),
        sa.Column("note_is_public", sa.Boolean(), nullable=True),
        sa.Column("is_main_sibling", sa.Boolean(), nullable=False),
        sa.Column("rom_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["rom_id"], ["roms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("rom_id", "user_id", name="unique_rom_user_props"),
    )

    op.execute(
        """
        INSERT INTO rom_user (id, updated_at, note_raw_markdown, note_is_public, is_main_sibling, rom_id, user_id)
        SELECT id, updated_at, raw_markdown, is_public, FALSE, rom_id, user_id
        FROM rom_notes
    """
    )

    op.drop_table("rom_notes")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "rom_notes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("raw_markdown", sa.Text(), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=True),
        sa.Column("rom_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["rom_id"], ["roms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("rom_id", "user_id", name="unique_rom_user_note"),
    )

    # Copy the data back from the new table to the old table
    op.execute(
        """
        INSERT INTO rom_notes (id, updated_at, raw_markdown, is_public, rom_id, user_id)
        SELECT id, updated_at, note_raw_markdown, note_is_public, rom_id, user_id
        FROM rom_user
    """
    )

    # Drop the new table
    op.drop_table("rom_user")
    # ### end Alembic commands ###
