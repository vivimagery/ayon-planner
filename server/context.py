import os
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from server import ProductionPlanner


class PlannerContext:
    addon: "ProductionPlanner"

    @property
    def schema_path(self) -> str:
        return os.path.join(
            self.addon.addon_dir,
            "server",
            "sql_schemas",
            "public.sql",
        )


context = PlannerContext()
