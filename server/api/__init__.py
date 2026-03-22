__all__ = ["init_endpoints"]

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ayon_server.addons import BaseServerAddon


from .events import (
    delete_planner_event,
    list_planner_events,
    save_planner_event,
    patch_planner_event,
)
from .scenarios import (
    delete_planner_scenario,
    list_planner_scenarios,
    save_planner_scenario,
    patch_planner_scenario,
)
from .tracks import (
    delete_planner_track,
    list_planner_tracks,
    save_planner_track,
    patch_planner_track,
)

from .tags import (
    list_planner_tags,
    save_planner_tag,
    patch_planner_tag,
    delete_planner_tag,
)
from .setup import get_project_planner_status, initialize_project_planner


def init_endpoints(addon: "BaseServerAddon") -> None:
    #
    # Tracks
    #

    addon.add_endpoint(
        "/tracks",
        list_planner_tracks,
        method="GET",
    )
    addon.add_endpoint(
        "/tracks",
        save_planner_track,
        method="POST",
    )
    addon.add_endpoint(
        "/tracks/{track_id}",
        patch_planner_track,
        method="PATCH",
    )
    addon.add_endpoint(
        "/tracks/{track_id}",
        delete_planner_track,
        method="DELETE",
    )

    #
    # Scenarios
    #

    addon.add_endpoint(
        "/scenarios",
        list_planner_scenarios,
        method="GET",
    )
    addon.add_endpoint(
        "/scenarios",
        save_planner_scenario,
        method="POST",
    )
    addon.add_endpoint(
        "/scenarios/{scenario_id}",
        patch_planner_scenario,
        method="PATCH",
    )
    addon.add_endpoint(
        "/scenarios/{scenario_id}",
        delete_planner_scenario,
        method="DELETE",
    )

    #
    # Events
    #

    addon.add_endpoint(
        "/events",
        list_planner_events,
        method="GET",
    )
    addon.add_endpoint(
        "/events",
        save_planner_event,
        method="POST",
    )
    addon.add_endpoint(
        "/events/{event_id}",
        patch_planner_event,
        method="PATCH",
    )
    addon.add_endpoint(
        "/events/{event_id}",
        delete_planner_event,
        method="DELETE",
    )

    #
    # Event tags
    #

    addon.add_endpoint(
        "/tags",
        list_planner_tags,
        method="GET",
    )

    addon.add_endpoint(
        "/tags",
        save_planner_tag,
        method="POST",
    )

    addon.add_endpoint(
        "/tags/{tag_name}",
        patch_planner_tag,
        method="PATCH",
    )

    addon.add_endpoint(
        "/tags/{tag_name}",
        delete_planner_tag,
        method="DELETE",
    )

    #
    # Setup
    #

    addon.add_endpoint(
        "/setup",
        get_project_planner_status,
        method="GET",
    )

    addon.add_endpoint(
        "/setup",
        initialize_project_planner,
        method="POST",
    )
