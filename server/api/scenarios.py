from ayon_server.api.dependencies import CurrentUser
from ayon_server.exceptions import NotFoundException
from ayon_server.lib.postgres import Postgres

from .models import PlannerScenario, PlannerScenarioPatchModel
from .dependencies import PlannerScenarioID, PlannerProjectName

from ..utils import table_reorder, normalize_positions


async def list_planner_scenarios(
    user: CurrentUser, project_name: PlannerProjectName
) -> list[PlannerScenario]:
    result = []
    async with Postgres.acquire() as conn, conn.transaction():
        if project_name:
            q = f"SET LOCAL search_path TO project_{project_name}"
            await conn.execute(q)
        q = "SELECT * FROM planner_scenarios ORDER BY position, label"
        for row in await conn.fetch(q):
            result.append(PlannerScenario(**row))
    return result


async def save_planner_scenario(
    user: CurrentUser,
    project_name: PlannerProjectName,
    payload: PlannerScenario,
) -> PlannerScenario:
    scenario_id = payload.id
    label = payload.label
    position = payload.position
    is_live = payload.is_live
    data = payload.data.dict(exclude_unset=True, exclude_defaults=True)

    async with Postgres.acquire() as conn, conn.transaction():
        if project_name:
            q = f"SET LOCAL search_path TO project_{project_name}"
            await conn.execute(q)

        if is_live:
            q = "UPDATE planner_scenarios SET is_live = FALSE WHERE is_live"
            await conn.execute(q)

        await conn.execute(
            """
            INSERT INTO planner_scenarios
                (id, label, position, is_live, data)
            VALUES
                ($1, $2, $3, $4, $5)
            """,
            scenario_id,
            label,
            9999,  # temporary position, will be updated later
            is_live,
            data,
        )

        await table_reorder("planner_scenarios", scenario_id, position, conn)
        await normalize_positions("planner_scenarios", conn)
    return payload


async def patch_planner_scenario(
    user: CurrentUser,
    project_name: PlannerProjectName,
    scenario_id: PlannerScenarioID,
    payload: PlannerScenarioPatchModel,
) -> None:
    async with Postgres.acquire() as conn, conn.transaction():
        if project_name:
            q = f"SET LOCAL search_path TO project_{project_name}"
            await conn.execute(q)

        res = await conn.fetch(
            "SELECT * FROM planner_scenarios WHERE id = $1",
            scenario_id,
        )

        if not res:
            raise NotFoundException("Track not found")

        if payload.is_live:
            q = "UPDATE planner_scenarios SET is_live = FALSE WHERE is_live"
            await conn.execute(q)

        scenario = PlannerScenario(**res[0])

        for field, value in payload.dict(exclude_unset=True).items():
            if field == "data":
                for data_field, data_value in value.items():
                    setattr(scenario.data, data_field, data_value)
                continue
            setattr(scenario, field, value)

        data_dict = scenario.data.dict(
            exclude_unset=True, exclude_defaults=True
        )

        await conn.execute(
            """
            UPDATE planner_scenarios
            SET
                label = $2,
                is_live = $3,
                data = $4
            WHERE id = $1
            """,
            scenario_id,
            scenario.label,
            scenario.is_live,
            data_dict,
        )

        if payload.position:
            await table_reorder(
                "planner_scenarios",
                scenario_id,
                payload.position,
                conn,
            )
            await normalize_positions("planner_scenarios", conn)


async def delete_planner_scenario(
    user: CurrentUser,
    project_name: PlannerProjectName,
    scenario_id: PlannerScenarioID,
) -> None:
    async with Postgres.acquire() as conn, conn.transaction():
        if project_name:
            q = f"SET LOCAL search_path TO project_{project_name}"
            await conn.execute(q)
        q = "DELETE FROM planner_scenarios WHERE id = $1"
        await conn.execute(q, scenario_id)
        await normalize_positions("planner_scenarios", conn)
