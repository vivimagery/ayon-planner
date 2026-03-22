from fastapi import Query

from ayon_server.api.dependencies import CurrentUser
from ayon_server.exceptions import NotFoundException
from ayon_server.lib.postgres import Postgres

from .models import PlannerTrack, PlannerTrackPatchModel
from .dependencies import PlannerTrackID, PlannerProjectName

from ..utils import table_reorder, normalize_positions


async def list_planner_tracks(
    user: CurrentUser,
    project_name: PlannerProjectName,
) -> list[PlannerTrack]:
    result = []
    async with Postgres.acquire() as conn, conn.transaction():
        if project_name:
            q = f"SET LOCAL search_path TO project_{project_name}"
            await conn.execute(q)

        q = "SELECT * FROM planner_tracks ORDER BY position, label"
        for row in await conn.fetch(q):
            result.append(PlannerTrack(**row))
    return result


async def save_planner_track(
    user: CurrentUser,
    project_name: PlannerProjectName,
    payload: PlannerTrack,
) -> PlannerTrack:
    track_id = payload.id
    label = payload.label
    position = payload.position
    is_default = payload.is_default
    data = payload.data.dict(exclude_unset=True, exclude_defaults=True)

    async with Postgres.acquire() as conn, conn.transaction():
        if project_name:
            q = f"SET LOCAL search_path TO project_{project_name}"
            await conn.execute(q)

        if payload.is_default:
            # We are setting this track as default,
            # so we need to unset the previous default track
            await conn.execute(
                """
                UPDATE planner_tracks
                SET is_default = FALSE
                WHERE is_default
                """
            )
        await conn.fetch(
            """
            INSERT INTO planner_tracks
            (id, label, position, is_default, data)
            VALUES ($1, $2, $3, $4, $5)
            """,
            track_id,
            label,
            9999,
            is_default,
            data,
        )

        await table_reorder("planner_tracks", track_id, position, conn)
        await normalize_positions("planner_tracks", conn)
    return payload


async def patch_planner_track(
    user: CurrentUser,
    project_name: PlannerProjectName,
    track_id: PlannerTrackID,
    payload: PlannerTrackPatchModel,
) -> None:
    async with Postgres.acquire() as conn, conn.transaction():
        if project_name:
            q = f"SET LOCAL search_path TO project_{project_name}"
            await conn.execute(q)

        res = await conn.fetch(
            "SELECT * FROM planner_tracks WHERE id = $1", track_id
        )

        if not res:
            raise NotFoundException("Track not found")

        if payload.is_default:
            # We are setting this track as default,
            # so we need to unset the previous default track
            q = "UPDATE planner_tracks SET is_default = FALSE WHERE is_default"
            await conn.execute(q)

        track = PlannerTrack(**res[0])

        for field, value in payload.dict(exclude_unset=True).items():
            if field == "data":
                for data_field, data_value in value.items():
                    setattr(track.data, data_field, data_value)
                continue
            setattr(track, field, value)

        data_dict = track.data.dict(exclude_unset=True, exclude_defaults=True)

        await conn.execute(
            """
            UPDATE planner_tracks
            SET
                label = $2,
                is_default = $3,
                data = $4
            WHERE id = $1
            """,
            track_id,
            track.label,
            track.is_default,
            data_dict,
        )

        if payload.position is not None:
            await table_reorder(
                "planner_tracks",
                track_id,
                payload.position,
                conn,
            )
            await normalize_positions("planner_tracks", conn)


async def delete_planner_track(
    user: CurrentUser,
    project_name: PlannerProjectName,
    track_id: PlannerTrackID,
    force: bool = Query(False, description="Delete with events"),
) -> None:
    async with Postgres.acquire() as conn, conn.transaction():
        if project_name:
            q = f"SET LOCAL search_path TO project_{project_name}"
            await conn.execute(q)

        if force:
            q = "DELETE FROM planner_events WHERE track_id = $1"
            await conn.execute(q, track_id)

        await conn.execute(
            "DELETE FROM planner_tracks WHERE id = $1", track_id
        )
        await normalize_positions("planner_tracks", conn)
