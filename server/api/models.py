from typing import Annotated
from datetime import datetime

from ayon_server.types import Field, OPModel
from ayon_server.utils import create_uuid

#
# Track
#


class PlannerTrackData(OPModel):
    color: Annotated[str | None, Field(example="#c0c0c0")] = None


class PlannerTrack(OPModel):
    id: Annotated[str, Field(default_factory=create_uuid)]
    label: Annotated[str, Field(...)]
    position: Annotated[int, Field(title="Track position")] = 0
    is_default: Annotated[bool, Field(title="Is default track")] = False
    data: Annotated[PlannerTrackData, Field(default_factory=PlannerTrackData)]


class PlannerTrackPatchModel(OPModel):
    label: Annotated[str | None, Field(title="Track label")] = None
    position: Annotated[int | None, Field(title="Track position")] = None
    is_default: Annotated[bool | None, Field(title="Is default track")] = None
    data: Annotated[PlannerTrackData | None, Field(title="Track data")] = None


#
# Scenario
#


class PlannerScenarioData(OPModel):
    color: str | None = Field(None, example="#c0c0c0")


class PlannerScenario(OPModel):
    id: str = Field(default_factory=create_uuid)
    label: str = Field(...)
    position: int = Field(0)
    is_live: bool = Field(False)
    data: PlannerScenarioData = Field(default_factory=PlannerScenarioData)


class PlannerScenarioPatchModel(OPModel):
    label: str | None = Field(None)
    position: int | None = Field(None)
    is_live: bool | None = Field(None)
    data: PlannerScenarioData | None = Field(None)


#
# Event
#


class PlannerEventData(OPModel):
    color: str | None = Field(None, example="#c0c0c0")


class PlannerEvent(OPModel):
    """
    Planner event model

    Both track_id and scenario_id are nullable.
    When scenario_id is not set, event will be displayed on all scenarios.
    """

    id: str = Field(
        default_factory=create_uuid,
        title="Event ID",
        example="af10c8f0e9b111e9b8f90242ac130003",
        min_length=32,
        max_length=32,
        regex=r"^[0-9a-f]{32}$",
    )
    event_type: str = Field(
        ...,
        title="Event type",
        example="milestone",
    )
    track_id: str | None = Field(
        None,
        title="Track ID",
        example="af10c8f0e9b111e9b8f90242ac130003",
        min_length=32,
        max_length=32,
        regex=r"^[0-9a-f]{32}$",
    )
    scenario_id: str | None = Field(
        None,
        title="Scenario ID",
        example="af10c8f0e9b111e9b8f90242ac130003",
        min_length=32,
        max_length=32,
        regex=r"^[0-9a-f]{32}$",
    )
    label: Annotated[str, Field(title="Event label")] = ""
    description: Annotated[str, Field(title="Event description")] = ""
    start_time: datetime = Field(...)
    end_time: datetime = Field(...)
    people: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    task_types: list[str] = Field(
        default_factory=list,
        example=["matchmove", "rigging"],
        description="Task types (project-level events only)",
    )
    data: PlannerEventData = Field(default_factory=PlannerEventData)


class PlannerEventPatchModel(OPModel):
    event_type: str | None = Field(None)
    track_id: str | None = Field(None)
    scenario_id: str | None = Field(None)
    label: str | None = Field(None)
    description: str | None = Field(None)
    start_time: datetime | None = Field(None)
    end_time: datetime | None = Field(None)
    people: list[str] | None = Field(None)
    tags: list[str] | None = Field(None)
    task_types: list[str] | None = Field(
        None, description="Task types (project-level events only)"
    )
    data: PlannerEventData | None = Field(None)
