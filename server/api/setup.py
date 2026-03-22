from ayon_server.api.dependencies import CurrentUser
from ayon_server.exceptions import BadRequestException, ForbiddenException
from ayon_server.lib.postgres import Postgres
from ayon_server.types import OPModel

from .dependencies import PlannerProjectName
from ..schema import ensure_planner_schema
from ..utils import ensure_project_exists


class PlannerProjectStatusItem(OPModel):
    name: str
    code: str
    initialized: bool


class PlannerProjectStatus(OPModel):
    projects: list[PlannerProjectStatusItem] | None = None
    initialized: bool


async def get_planner_project_list(user: CurrentUser) -> PlannerProjectStatus:
    q = """
        SELECT
            t.schemaname AS schemaname,
            p.name AS project_name,
            p.code AS project_code
        FROM projects p
        LEFT JOIN pg_tables t
            ON LOWER(t.schemaname) = LOWER('project_' || p.name)
            AND p.active
            AND tablename = 'planner_tracks'
        ORDER BY p.name
    """

    projects = []
    async for row in Postgres.iterate(q):
        project_name = row["project_name"]
        project_code = row["project_code"]

        if project_name is None:
            continue

        try:
            user.check_project_access(project_name)
        except ForbiddenException:
            continue

        projects.append(
            PlannerProjectStatusItem(
                name=project_name,
                code=project_code,
                initialized=bool(row["schemaname"]),
            )
        )

    return PlannerProjectStatus(initialized=True, projects=projects)


async def ensure_project_initialized(
    project_name: str,
) -> PlannerProjectStatus:
    q = "SELECT * FROM pg_tables WHERE schemaname = $1 AND tablename = $2"
    result = await Postgres.fetch(
        q, f"project_{project_name.lower()}", "planner_tracks"
    )
    initialized = len(result) > 0
    return PlannerProjectStatus(initialized=initialized)


async def get_project_planner_status(
    user: CurrentUser,
    project_name: PlannerProjectName,
) -> PlannerProjectStatus:
    """Check whether a given project has a planner schema initialized.

    If no project name is provided, return the status for all projects.
    """
    if project_name:
        return await ensure_project_initialized(project_name)

    return await get_planner_project_list(user)


async def initialize_project_planner(
    user: CurrentUser,
    project_name: PlannerProjectName,
) -> PlannerProjectStatus:
    """Initialize the planner schema for a given project."""

    if project_name is None:
        raise BadRequestException("Project name is required")

    await ensure_project_exists(project_name)
    await ensure_planner_schema(project_name=project_name)
    return PlannerProjectStatus(initialized=True)
