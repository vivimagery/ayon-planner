from ayon_server.helpers.project_list import get_project_list
from ayon_server.exceptions import NotFoundException
from ayon_server.lib.postgres import Connection


async def ensure_project_exists(project_name: str) -> None:
    projects = await get_project_list()
    for project in projects:
        if project.name == project_name:
            return
    raise NotFoundException(f"Project {project_name }not found")


async def normalize_positions(table_name: str, conn: Connection) -> None:
    query = f"""
    WITH normalized_positions AS (
        SELECT id, ROW_NUMBER() OVER (ORDER BY position) AS new_pos
        FROM {table_name}
    )
    UPDATE {table_name} t
    SET position = np.new_pos
    FROM normalized_positions np
    WHERE t.id = np.id;
    """
    await conn.execute(query)


async def table_reorder(
    table_name: str, row_id: str, order: int, conn: Connection
) -> None:
    """Reorder a row in a table"""

    query = f"""

    -- Get the old position of the track we're moving
    WITH track_info AS (
        SELECT position as old_position
        FROM {table_name} WHERE id = $1
    )

    UPDATE {table_name}
    SET position =
        CASE
            -- The track we're moving
            WHEN id = $1 THEN $2

            -- Moving track down (increasing position)
            WHEN position > (SELECT old_position FROM track_info)
                AND position <= $2 THEN
                position - 1

            -- Moving track up (decreasing position)
            WHEN position >= $2
                AND position < (SELECT old_position FROM track_info) THEN
                position + 1

            -- Other tracks remain unchanged
            ELSE position
        END
    WHERE
        position
            BETWEEN LEAST($2, (SELECT old_position FROM track_info))
            AND GREATEST($2, (SELECT old_position FROM track_info))
    OR
        id = $1;
    """

    await conn.execute(query, row_id, order)
