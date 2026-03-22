import uuid
import json
import os

from ayon_server.addons.addon import BaseServerAddon
from ayon_server.entities.user import UserEntity
from ayon_server.exceptions import ConflictException

from nxtools import logging, log_traceback

from .api.events import save_planner_event
from .api.models import PlannerEvent, PlannerTrack
from .api.tracks import save_planner_track


def create_track_id(label: str) -> str:
    return uuid.uuid5(uuid.NAMESPACE_DNS, label).hex


async def create_demo_data(addon: BaseServerAddon, user: UserEntity) -> None:
    private_dir = addon.get_private_dir()
    demo_dir = os.path.join(private_dir, "demo")

    for i, lang_code in enumerate(["cz", "fr", "de"]):
        country_name = {
            "cz": "Czechia",
            "fr": "France",
            "de": "Germany",
        }[lang_code]

        people = {
            "cz": ["Jakub", "Milan"],
            "fr": ["Pierre", "Jeanne"],
            "de": ["Helmut", "Greta"],
        }[lang_code]

        track_id = create_track_id(f"holidays-{lang_code}")

        track = PlannerTrack(
            id=track_id,
            label=f"Holidays in {country_name}",
            position=i + 1,
        )

        try:
            await save_planner_track(user, None, track)
        except ConflictException:
            log_traceback()
            pass

        demo_path = os.path.join(demo_dir, f"holidays-{lang_code}.json")
        data = json.load(open(demo_path))
        logging.debug(f"Loaded {len(data)} records from {demo_path}")
        for rec in data:
            logging.debug(f"Processing record {rec['id']}")
            title = rec["name"][0]["text"]
            start_time = rec["startDate"] + "T00:00:00Z"
            end_time = rec["endDate"] + "T23:59:59Z"

            event = PlannerEvent(
                id=rec["id"].replace("-", ""),
                label=title,
                event_type="holiday",
                start_time=start_time,
                end_time=end_time,
                track_id=track_id,
                people=people,
            )

            try:
                await save_planner_event(user, None, event)
            except ConflictException:
                logging.debug(f"Event {event.id} already exists")
                pass
