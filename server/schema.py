import aiofiles
from nxtools import logging

from ayon_server.lib.postgres import Postgres, Connection
from ayon_server.helpers.project_list import get_project_list

from .context import context


async def _drop_planner_schema(conn: Connection) -> None:
    await conn.execute("DROP TABLE IF EXISTS planner_tracks CASCADE")
    await conn.execute("DROP TABLE IF EXISTS planner_scenarios CASCADE")
    await conn.execute("DROP TABLE IF EXISTS planner_events CASCADE")


async def _ensure_planner_schema(conn: Connection) -> None:
    # Ensure schema is created and up to date
    async with aiofiles.open(context.schema_path, mode="r") as f:
        schema = await f.read()
        await conn.execute(schema)


async def drop_planner_schema(project_name: str | None = None) -> None:
    projects = await get_project_list()
    async with Postgres.acquire() as conn, conn.transaction():
        if project_name:
            q = f"SET LOCAL search_path TO project_{project_name}"
            await conn.execute(q)
            logging.debug(f"Dropping project {project_name} planner schema")
            await _drop_planner_schema(conn)

        else:
            logging.debug("Dropping public planner schema")
            await _drop_planner_schema(conn)

            for project in projects:
                q = f"SET LOCAL search_path TO project_{project.name}"
                await conn.execute(q)
                logging.debug(f"Dropping project {project} planner schema")
                await _drop_planner_schema(conn)


async def ensure_planner_schema(project_name: str | None = None) -> None:
    async with Postgres.acquire() as conn, conn.transaction():
        if project_name:
            q = f"SET LOCAL search_path TO project_{project_name}"
            await conn.execute(q)
        await _ensure_planner_schema(conn)
