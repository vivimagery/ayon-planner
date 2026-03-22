from typing import Any
from pydantic import validator

from ayon_server.settings import BaseSettingsModel, SettingsField
from ayon_server.settings.validators import ensure_unique_names


class ColorPresets(BaseSettingsModel):
    red: str = SettingsField("#cd3535", title="Red", widget="color")
    orange: str = SettingsField("#d95a1f", title="Orange", widget="color")
    yellow: str = SettingsField("#ebc13a", title="Yellow", widget="color")
    green: str = SettingsField("#13b76d", title="Green", widget="color")
    blue: str = SettingsField("#0094d8", title="Blue", widget="color")
    purple: str = SettingsField("#ac36c3", title="Purple", widget="color")


class EventTag(BaseSettingsModel):
    _layout = "compact"
    name: str = SettingsField(..., title="Name", min_length=1, max_length=50)
    color: str = SettingsField("#ac36c3", title="Color", widget="color")


class ProductionPlannerSettings(BaseSettingsModel):
    color_presets: ColorPresets = SettingsField(
        default_factory=ColorPresets,
        title="Color Presets",
    )

    tags: list[EventTag] = SettingsField(
        default_factory=list,
        title="Tags",
        description="Tags to categorize events",
    )

    @validator("tags")
    def ensure_unique_names(cls, value: Any, field: Any) -> list[EventTag]:
        ensure_unique_names(value, field_name=field.name)
        return value
