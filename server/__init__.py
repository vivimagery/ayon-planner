from ayon_server.addons import BaseServerAddon
from ayon_server.api.dependencies import CurrentUser  # dev only


from .api import init_endpoints
from .api.dependencies import PlannerProjectName
from .demo import create_demo_data  # dev only

from .context import context
from .settings import ProductionPlannerSettings
from .schema import ensure_planner_schema, drop_planner_schema

from typing import Any


class ProductionPlanner(BaseServerAddon):
    settings_model = ProductionPlannerSettings
    addon_type = "server"
    frontend_scopes: dict[str, Any] = {"dashboard": {}, "project": {}}

    def initialize(self) -> None:
        context.addon = self
        init_endpoints(self)

        # Development endpoints
        self.add_endpoint("/reset", self.planner_reset, method="POST")
        self.add_endpoint("/demo", self.deploy_demo, method="POST")

    async def get_default_settings(self) -> ProductionPlannerSettings:
        settings_model_cls = self.get_settings_model()
        return settings_model_cls()

    async def setup(self) -> None:
        try:
            await ensure_planner_schema()
        except Exception:
            await drop_planner_schema()
            await ensure_planner_schema()

    # Development endpoints

    async def planner_reset(
        self, _: CurrentUser, project_name: PlannerProjectName
    ) -> None:
        await drop_planner_schema(project_name)
        # enure public schema exists, keep project schemas dropped
        await ensure_planner_schema()

    async def deploy_demo(self, user: CurrentUser) -> None:
        await create_demo_data(self, user)
