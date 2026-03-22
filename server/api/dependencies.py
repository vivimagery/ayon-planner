from typing import Annotated

from fastapi import Depends, Path, Query

from ..utils import ensure_project_exists


def dep_planner_event_id(
    event_id: str = Path(
        ...,
        title="Event ID",
        example="af10c8f0e9b111e9b8f90242ac130003",
        min_length=32,
        max_length=32,
        regex=r"^[0-9a-f]{32}$",
    ),
) -> str:
    return event_id


def dep_planner_track_id(
    track_id: str = Path(
        ...,
        title="Track ID",
        example="af10c8f0e9b111e9b8f90242ac130003",
        min_length=32,
        max_length=32,
        regex=r"^[0-9a-f]{32}$",
    ),
) -> str:
    return track_id


def dep_planner_scenario_id(
    scenario_id: str = Path(
        ...,
        title="Scenario ID",
        example="af10c8f0e9b111e9b8f90242ac130003",
        min_length=32,
        max_length=32,
        regex=r"^[0-9a-f]{32}$",
    ),
) -> str:
    return scenario_id


async def dep_optional_project_name(
    project_name: str | None = Query(
        None,
        title="Project Name",
        example="My Project",
        alias="project",
    ),
) -> str | None:
    if project_name is None:
        return None
    await ensure_project_exists(project_name)
    return project_name


PlannerEventID = Annotated[str, Depends(dep_planner_event_id)]
PlannerTrackID = Annotated[str, Depends(dep_planner_track_id)]
PlannerScenarioID = Annotated[str, Depends(dep_planner_scenario_id)]
PlannerProjectName = Annotated[str | None, Depends(dep_optional_project_name)]
