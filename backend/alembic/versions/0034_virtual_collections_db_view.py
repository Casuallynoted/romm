"""empty message

Revision ID: 0034_virtual_collections_db_view
Revises: 0033_rom_file_and_hashes
Create Date: 2024-08-08 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from utils.database import CustomJSON, is_postgresql

# revision identifiers, used by Alembic.
revision = "0034_virtual_collections_db_view"
down_revision = "0033_rom_file_and_hashes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "collections_roms",
        sa.Column("collection_id", sa.Integer(), nullable=False),
        sa.Column("rom_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["collection_id"], ["collections.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["rom_id"], ["roms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("collection_id", "rom_id"),
        sa.UniqueConstraint("collection_id", "rom_id", name="unique_collection_rom"),
    )

    connection = op.get_bind()

    if is_postgresql(connection):
        connection.execute(
            sa.text(
                """
                INSERT INTO collection_roms (collection_id, rom_id)
                SELECT c.id, rom_id::INT, NOW(), NOW()
                FROM collections c,
                LATERAL jsonb_array_elements_text(c.roms) AS rom_id
                """
            )
        )
        connection.execute(
            sa.text(
                """
                CREATE OR REPLACE VIEW virtual_collections AS
                WITH genres_collection AS (
                    SELECT 
                        r.id as rom_id,
                        r.path_cover_s as path_cover_s,
                        r.path_cover_l as path_cover_l,
                        jsonb_array_elements_text(to_jsonb(igdb_metadata ->> 'genres')) as collection_name,
                        'genre' as collection_type
                    FROM roms r
                    WHERE igdb_metadata->>'genres' IS NOT NULL
                ),
                franchises_collection AS (
                    SELECT 
                        r.id as rom_id,
                        r.path_cover_s as path_cover_s,
                        r.path_cover_l as path_cover_l,
                        jsonb_array_elements_text(to_jsonb(igdb_metadata->>'franchises')) as collection_name,
                        'franchise' as collection_type
                    FROM roms r
                    WHERE igdb_metadata->>'franchises' IS NOT NULL
                ),
                collection_collection AS (
                    SELECT 
                        r.id as rom_id,
                        r.path_cover_s as path_cover_s,
                        r.path_cover_l as path_cover_l,
                        jsonb_array_elements_text(to_jsonb(igdb_metadata->>'collections')) as collection_name,
                        'collection' as collection_type
                    FROM roms r
                    WHERE igdb_metadata->>'collections' IS NOT NULL
                ),
                modes_collection AS (
                    SELECT 
                        r.id as rom_id,
                        r.path_cover_s as path_cover_s,
                        r.path_cover_l as path_cover_l,
                        jsonb_array_elements_text(to_jsonb(igdb_metadata->>'game_modes')) as collection_name,
                        'mode' as collection_type
                    FROM roms r
                    WHERE igdb_metadata->>'game_modes' IS NOT NULL
                ),
                companies_collection AS (
                    SELECT 
                        r.id as rom_id,
                        r.path_cover_s as path_cover_s,
                        r.path_cover_l as path_cover_l,
                        jsonb_array_elements_text(to_jsonb(igdb_metadata->>'companies')) as collection_name,
                        'company' as collection_type
                    FROM roms r
                    WHERE igdb_metadata->>'companies' IS NOT NULL
                )
                SELECT 
                collection_name as name,
                collection_type as type,
                'Autogenerated ' || collection_type || ' collection' AS description,
                NOW() AS created_at,
                NOW() AS updated_at,
                array_to_json(array_agg(DISTINCT rom_id)) as rom_ids,
                array_to_json(array_agg(DISTINCT path_cover_s)) as path_covers_s,
                array_to_json(array_agg(DISTINCT path_cover_l)) as path_covers_l
                FROM (
                    SELECT * FROM genres_collection
                    UNION ALL
                    SELECT * FROM franchises_collection
                    UNION ALL
                    SELECT * FROM collection_collection
                    UNION ALL
                    SELECT * FROM modes_collection
                    UNION ALL
                    SELECT * FROM companies_collection
                ) combined
                GROUP BY collection_type, collection_name
                HAVING COUNT(DISTINCT rom_id) > 2
                ORDER BY collection_type, collection_name;
                """  # nosec B608
            ),
        )
    else:
        connection.execute(
            sa.text(
                """
                INSERT INTO collections_roms (collection_id, rom_id, created_at, updated_at)
                SELECT c.id, jt.rom_id, NOW(), NOW()
                FROM collections c
                JOIN JSON_TABLE(c.roms, '$[*]' COLUMNS (rom_id INT PATH '$')) AS jt
                """
            )
        )
        connection.execute(
            sa.text(
                """
                CREATE OR REPLACE VIEW virtual_collections AS 
                WITH genres AS (
                    SELECT
                        r.id as rom_id,
                        r.path_cover_s as path_cover_s,
                        r.path_cover_l as path_cover_l,
                        CONCAT(j.genre) as collection_name,
                        'genre' as collection_type
                    FROM
                        roms r
                        CROSS JOIN JSON_TABLE(
                            JSON_EXTRACT(igdb_metadata, '$.genres'),
                            '$[*]' COLUMNS (genre VARCHAR(255) PATH '$')
                        ) j
                    WHERE
                        JSON_EXTRACT(igdb_metadata, '$.genres') IS NOT NULL
                ),
                franchises AS (
                    SELECT
                        r.id as rom_id,
                        r.path_cover_s as path_cover_s,
                        r.path_cover_l as path_cover_l,
                        CONCAT(j.franchise) as collection_name,
                        'franchise' as collection_type
                    FROM
                        roms r
                        CROSS JOIN JSON_TABLE(
                            JSON_EXTRACT(igdb_metadata, '$.franchises'),
                            '$[*]' COLUMNS (franchise VARCHAR(255) PATH '$')
                        ) j
                    WHERE
                        JSON_EXTRACT(igdb_metadata, '$.franchises') IS NOT NULL
                ),
                collections AS (
                    SELECT
                        r.id as rom_id,
                        r.path_cover_s as path_cover_s,
                        r.path_cover_l as path_cover_l,
                        CONCAT(j.collection) as collection_name,
                        'collection' as collection_type
                    FROM
                        roms r
                        CROSS JOIN JSON_TABLE(
                            JSON_EXTRACT(igdb_metadata, '$.collections'),
                            '$[*]' COLUMNS (collection VARCHAR(255) PATH '$')
                        ) j
                    WHERE
                        JSON_EXTRACT(igdb_metadata, '$.collections') IS NOT NULL
                ),
                modes AS (
                    SELECT
                        r.id as rom_id,
                        r.path_cover_s as path_cover_s,
                        r.path_cover_l as path_cover_l,
                        CONCAT(j.mode) as collection_name,
                        'mode' as collection_type
                    FROM
                        roms r
                        CROSS JOIN JSON_TABLE(
                            JSON_EXTRACT(igdb_metadata, '$.game_modes'),
                            '$[*]' COLUMNS (mode VARCHAR(255) PATH '$')
                        ) j
                    WHERE
                        JSON_EXTRACT(igdb_metadata, '$.game_modes') IS NOT NULL
                ),
                companies AS (
                    SELECT
                        r.id as rom_id,
                        r.path_cover_s as path_cover_s,
                        r.path_cover_l as path_cover_l,
                        CONCAT(j.company) as collection_name,
                        'company' as collection_type
                    FROM
                        roms r
                        CROSS JOIN JSON_TABLE(
                            JSON_EXTRACT(igdb_metadata, '$.companies'),
                            '$[*]' COLUMNS (company VARCHAR(255) PATH '$')
                        ) j
                    WHERE
                        JSON_EXTRACT(igdb_metadata, '$.companies') IS NOT NULL
                )
                SELECT
                    collection_name as name,
                    collection_type as type,
                    CONCAT('Autogenerated ', collection_name, ' collection') AS description,
                    NOW() AS created_at,
                    NOW() AS updated_at,
                    JSON_ARRAYAGG(DISTINCT rom_id) as rom_ids,
                    JSON_ARRAYAGG(DISTINCT path_cover_s) as path_covers_s,
                    JSON_ARRAYAGG(DISTINCT path_cover_l) as path_covers_l
                FROM
                (
                    SELECT * FROM genres
                    UNION ALL
                    SELECT * FROM franchises
                    UNION ALL
                    SELECT * FROM collections
                    UNION ALL
                    SELECT * FROM modes
                    UNION ALL
                    SELECT * FROM companies
                ) combined
                GROUP BY collection_type, collection_name
                HAVING COUNT(DISTINCT rom_id) > 2
                ORDER BY collection_type, collection_name;
                """
            ),
        )

    op.drop_column("collections", "roms")


def downgrade() -> None:
    with op.batch_alter_table("collections", schema=None) as batch_op:
        batch_op.add_column(sa.Column("roms", CustomJSON(), nullable=False))

    connection = op.get_bind()
    if is_postgresql(connection):
        connection.execute(
            sa.text(
                """
                UPDATE collections c
                SET roms = (
                    SELECT jsonb_agg(rom_id)
                    FROM collections_roms cr
                    WHERE cr.collection_id = c.id
                );
                """
            )
        )
    else:
        connection.execute(
            sa.text(
                """
                UPDATE collections c
                JOIN (
                    SELECT collection_id, JSON_ARRAYAGG(rom_id) as roms
                    FROM collections_roms
                    GROUP BY collection_id
                ) cr
                ON c.id = cr.collection_id
                SET c.roms = cr.roms;
                """
            )
        )

    op.drop_table("collections_roms")

    connection.execute(
        sa.text(
            """
            DROP VIEW virtual_collections;
            """
        ),
    )
