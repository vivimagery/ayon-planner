from ayon_server.api.dependencies import CurrentUser
from ayon_server.exceptions import BadRequestException, NotFoundException
from ayon_server.lib.postgres import Connection, Postgres
from ayon_server.types import OPModel
from fastapi import Path

from ..context import context
from ..settings import EventTag
from ..utils import ensure_project_exists
from .dependencies import PlannerProjectName


async def _list_tags(
    project_name: str | None, with_colors: bool = False
) -> list[EventTag]:
    addon = context.addon
    if project_name is None:
        settings = await addon.get_studio_settings()
    else:
        await ensure_project_exists(project_name)
        settings = await addon.get_project_settings(project_name)
    tags: list[EventTag] = []
    if with_colors:
        for key, value in settings.color_presets.dict().items():
            tags.append(EventTag(name=f"__{key}", color=value))
    tags.extend(settings.tags)
    return tags


async def _set_tag_settings(
    project_name: str | None,
    tags: list[EventTag],
    conn: Connection | None = None,
) -> None:
    addon = context.addon
    schema = "public" if project_name is None else f"project_{project_name}"
    payload = [tag.dict() for tag in tags]
    query = f"""
        INSERT INTO {schema}.settings
            (addon_name, addon_version, variant, data)
        VALUES
            ($1, $2, $3, jsonb_set('{{}}'::JSONB, '{{tags}}',  $4))
        ON CONFLICT (addon_name, addon_version, variant)
        DO UPDATE SET
            data = jsonb_set(settings.data, '{{tags}}', $4)
    """

    if conn is None:
        await Postgres.execute(
            query, addon.name, addon.version, "production", payload
        )
    else:
        await conn.execute(
            query, addon.name, addon.version, "production", payload
        )
    # TODO: dispatch event that settings have changed
    # Or not? Because it will flood the log with unnecessary events


#
# [GET] /tags
#


async def list_planner_tags(
    user: CurrentUser,
    project_name: PlannerProjectName,
) -> list[EventTag]:
    """List all stored event tags"""
    return await _list_tags(project_name, with_colors=True)


#
# [POST] /tags
#


class EventTagPostModel(OPModel):
    name: str
    color: str | None = None


async def save_planner_tag(
    user: CurrentUser,
    project_name: PlannerProjectName,
    payload: EventTagPostModel,
) -> None:
    """Create or update an event tag.

    if a tag with the same name already exists, it will be updated.
    """

    if payload.name.startswith("__"):
        raise BadRequestException("Cannot create or update a virtual tag")
    if not payload.name:
        raise BadRequestException("Name cannot be empty")

    existing_tags = await _list_tags(project_name, False)
    for etag in existing_tags:
        if etag.name != payload.name:
            continue

        if payload.color is not None:
            etag.color = etag.color
        break

    else:
        existing_tags.append(EventTag(name=payload.name, color=payload.color))
    await _set_tag_settings(project_name, existing_tags)


#
# [PATCH] /tags/{tag_name}
#


class EventTagPatchModel(OPModel):
    name: str | None = None
    color: str | None = None


async def patch_planner_tag(
    user: CurrentUser,
    project_name: PlannerProjectName,
    payload: EventTagPatchModel,
    tag_name: str = Path(...),
) -> None:
    if payload.name is not None:
        if payload.name.startswith("__"):
            raise BadRequestException("Cannot create or update a virtual tag")
        if not payload.name:
            raise BadRequestException("Name cannot be empty")

    if tag_name.startswith("__"):
        raise BadRequestException("Cannot create or update a virtual tag")

    async with Postgres.acquire() as conn, conn.transaction():
        existing_tags = await _list_tags(project_name, False)
        for etag in existing_tags:
            if etag.name != tag_name:
                continue
            if payload.color is not None:
                etag.color = payload.color

            if payload.name is not None:
                etag.name = payload.name
            break

        else:
            raise NotFoundException("Tag not found")

        await _set_tag_settings(project_name, existing_tags, conn)

        # Renaming a tag requires updating all events that use it
        if payload.name is not None:
            schema = (
                "public" if project_name is None else f"project_{project_name}"
            )
            q = f"""
                UPDATE {schema}.planner_events
                SET tags = array_replace(tags, $1, $2)
                WHERE $1 = ANY(tags)
            """
            await conn.execute(q, tag_name, payload.name)


#
# [DELETE] /tags/{tag_name}
#


async def delete_planner_tag(
    user: CurrentUser,
    project_name: PlannerProjectName,
    tag_name: str = Path(...),
) -> None:
    existing_tags = await _list_tags(project_name, False)
    new_tags = [tag for tag in existing_tags if tag.name != tag_name]

    async with Postgres.acquire() as conn, conn.transaction():
        if len(new_tags) != len(existing_tags):
            await _set_tag_settings(project_name, new_tags, conn)

        # regardless the tag was present in the settings or not,
        # we need to update all events that use it

        schema = (
            "public" if project_name is None else f"project_{project_name}"
        )
        q = f"""
            UPDATE {schema}.planner_events
            SET tags = array_remove(tags, $1)
            WHERE $1 = ANY(tags)
        """
        await conn.execute(q, tag_name)
