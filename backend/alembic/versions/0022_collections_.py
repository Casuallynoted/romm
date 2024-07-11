"""empty message

Revision ID: 0022_collections
Revises: 0021_rom_user
Create Date: 2024-07-01 23:23:39.090219

"""

import json
import os
import shutil

import sqlalchemy as sa
from alembic import op
from config import RESOURCES_BASE_PATH
from sqlalchemy import inspect
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "0022_collections"
down_revision = "0021_rom_user"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###

    # Doing first the resources migration to avoid orphan collections table if migration fails
    connection = op.get_bind()
    roms = connection.execute(
        sa.text(
            "SELECT id, name, platform_id, path_cover_s, path_cover_l, path_screenshots FROM roms"
        )
    ).fetchall()

    # Define the path for the new folder
    roms_folder_path = os.path.join(RESOURCES_BASE_PATH, "roms")

    # Create the new folder if it doesn't exist
    os.makedirs(roms_folder_path, exist_ok=True)

    # List all items in the base directory
    for folder in os.listdir(RESOURCES_BASE_PATH):
        folder_path = os.path.join(RESOURCES_BASE_PATH, folder)

        # Check if the item is a directory and not the new folder itself
        if os.path.isdir(folder_path) and folder != "roms":
            # Move the folder to the new folder
            shutil.move(folder_path, roms_folder_path)

    # Update paths for each rom
    for rom in roms:
        path_cover_s = rom.path_cover_s
        path_cover_l = rom.path_cover_l
        path_screenshots = rom.path_screenshots

        # Add "roms/" prefix to path_cover_s and path_cover_l
        if path_cover_s:
            path_cover_s = f"roms/{path_cover_s}"
        if path_cover_l:
            path_cover_l = f"roms/{path_cover_l}"

        # Add "roms/" prefix to each path in path_screenshots
        if path_screenshots:
            path_screenshots_list = json.loads(path_screenshots)
            path_screenshots_list = [f"roms/{path}" for path in path_screenshots_list]
            path_screenshots = json.dumps(path_screenshots_list)

        # Update the database with the new paths
        connection.execute(
            sa.text(
                "UPDATE roms SET path_cover_s = :path_cover_s, path_cover_l = :path_cover_l, path_screenshots = :path_screenshots WHERE id = :id"
            ),
            {
                "path_cover_s": path_cover_s,
                "path_cover_l": path_cover_l,
                "path_screenshots": path_screenshots,
                "id": rom.id,
            },
        )

    inspector = inspect(connection)
    if not inspector.has_table("collections"):
        op.create_table(
            "collections",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(length=400), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("path_cover_l", sa.String(length=1000), nullable=True),
            sa.Column("path_cover_s", sa.String(length=1000), nullable=True),
            sa.Column("url_cover", sa.Text(), nullable=True),
            sa.Column("roms", sa.JSON(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("is_public", sa.Boolean(), nullable=False),
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
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    with op.batch_alter_table("rom_user", schema=None) as batch_op:
        batch_op.alter_column(
            "is_main_sibling",
            existing_type=mysql.TINYINT(display_width=1),
            nullable=True,
        )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("rom_user", schema=None) as batch_op:
        batch_op.alter_column(
            "is_main_sibling",
            existing_type=mysql.TINYINT(display_width=1),
            nullable=False,
        )

    op.drop_table("collections")
    # ### end Alembic commands ###