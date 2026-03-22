from datetime import datetime

from ayon_server.exceptions import NotFoundException
from ayon_server.api.dependencies import CurrentUser
from ayon_server.lib.postgres import Postgres
from ayon_server.types import (
    sanitize_string_list,
    validate_user_name_list,
)
from ayon_server.utils import SQLTool
from fastapi import Query

from .models import PlannerEvent, PlannerEventPatchModel
from .dependencies import PlannerEventID, PlannerProjectName


async def list_planner_events(
    user: CurrentUser,
    project_name: PlannerProjectName,
    start_time: datetime | None = Query(
        None, example="2024-01-01T00:00:00Z", alias="from"
    ),
    end_time: datetime | None = Query(
        None, example="2024-12-31T23:59:59Z", alias="to"
    ),
    track_id: str | None = Query(None, alias="track"),
    scenario_id: str | None = Query(None, alias="scenario"),
    tags: list[str] | None = Query(None, example=["holiday"]),
    people: list[str] | None = Query(
        None, example=["albus", "severus", "harry"]
    ),
) -> list[PlannerEvent]:
    result = []
    conditions = []

    # TODO: proper sanitization

    if start_time:
        conditions.append(f"start_time >= '{start_time.isoformat()}'")
    if end_time:
        conditions.append(f"end_time <= '{end_time.isoformat()}'")
    if track_id:
        conditions.append(f"track_id = '{track_id}'")

    if scenario_id:
        conditions.append(
            f"(scenario_id = '{scenario_id}' OR scenario_id IS NULL)"
        )
    else:
        conditions.append("scenario_id IS NULL")

    if tags is not None:
        sanitize_string_list(tags)
        conditions.append(f"tags && {SQLTool.array(tags, curly=True)}")

    if people is not None:
        validate_user_name_list(people)
        conditions.append(f"people && {SQLTool.array(people, curly=True)}")

    full_conditions = " AND ".join(conditions)

    query = f"""
        SELECT * FROM planner_events
        WHERE {full_conditions}
        ORDER BY start_time ASC
    """

    async with Postgres.acquire() as conn, conn.transaction():
        if project_name:
            q = f"SET LOCAL search_path TO project_{project_name}"
            await conn.execute(q)

        for row in await conn.fetch(query):
            result.append(PlannerEvent(**row))
    return result


async def save_planner_event(
    user: CurrentUser,
    project_name: PlannerProjectName,
    payload: PlannerEvent,
) -> PlannerEvent:
    async with Postgres.acquire() as conn, conn.transaction():
        if project_name:
            q = f"SET LOCAL search_path TO project_{project_name}"
            await conn.execute(q)
        await conn.execute(
            """
            INSERT INTO planner_events
                (
                    id,
                    event_type,
                    track_id,
                    scenario_id,
                    label,
                    description,
                    start_time,
                    end_time,
                    people,
                    task_types,
                    tags
                )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
            payload.id,
            payload.event_type,
            payload.track_id,
            payload.scenario_id,
            payload.label,
            payload.description,
            payload.start_time,
            payload.end_time,
            payload.people,
            payload.task_types,
            payload.tags,
        )
    return payload


async def patch_planner_event(
    user: CurrentUser,
    project_name: PlannerProjectName,
    event_id: PlannerEventID,
    payload: PlannerEventPatchModel,
) -> None:
    async with Postgres.acquire() as conn, conn.transaction():
        if project_name:
            q = f"SET LOCAL search_path TO project_{project_name}"
            await conn.execute(q)

        # get the event

        res = await conn.fetch(
            "SELECT * FROM planner_events WHERE id = $1", event_id
        )

        if not res:
            raise NotFoundException("Event not found")

        event = PlannerEvent(**res[0])

        # apply the patch

        for field, value in payload.dict(exclude_unset=True).items():
            if field == "people" or field == "tags":
                value = value or []

            elif field == "data":
                for data_field, data_value in value.items():
                    setattr(event.data, data_field, data_value)
                continue
            setattr(event, field, value)

        # save the event

        await conn.execute(
            """
            UPDATE planner_events
            SET
                event_type = $2,
                track_id = $3,
                scenario_id = $4,
                label = $5,
                description = $6,
                start_time = $7,
                end_time = $8,
                people = $9,
                task_types = $10,
                tags = $11
            WHERE id = $1
            """,
            event.id,
            event.event_type,
            event.track_id,
            event.scenario_id,
            event.label,
            event.description,
            event.start_time,
            event.end_time,
            event.people,
            event.task_types,
            event.tags,
        )


async def delete_planner_event(
    user: CurrentUser,
    project_name: PlannerProjectName,
    event_id: PlannerEventID,
) -> None:
    async with Postgres.acquire() as conn, conn.transaction():
        if project_name:
            q = f"SET LOCAL search_path TO project_{project_name}"
            await conn.execute(q)
        q = "DELETE FROM planner_events WHERE id = $1"
        await conn.execute(q, event_id)
