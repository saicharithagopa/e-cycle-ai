"""Knowledge service.

Interface: get_profile(db, device_class_name) -> DeviceProfileData.
Loads the versioned, curated profile for a device class. Profiles describe
*typical* components and materials for the class — they are category-level
estimates, never measurements of a specific unit.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import DeviceClass, DeviceProfile


class ProfileNotFoundError(LookupError):
    """Raised when no curated profile exists for the requested class."""


@dataclass(frozen=True)
class DeviceProfileData:
    device_class: str
    version: str
    components: list[dict]
    materials: list[dict]
    hazards: list[str]
    caveats: str


def get_profile(db: Session, device_class_name: str) -> DeviceProfileData:
    """Return the latest curated profile for a device class."""
    profile = db.execute(
        select(DeviceProfile)
        .join(DeviceClass, DeviceProfile.device_class_id == DeviceClass.id)
        .where(DeviceClass.name == device_class_name)
        .order_by(DeviceProfile.id.desc())
    ).scalar_one_or_none()
    if profile is None:
        raise ProfileNotFoundError(
            f"No curated knowledge profile for device class '{device_class_name}'."
        )
    return DeviceProfileData(
        device_class=device_class_name,
        version=profile.version,
        components=json.loads(profile.components_json),
        materials=json.loads(profile.materials_json),
        hazards=json.loads(profile.hazards_json),
        caveats=profile.caveats,
    )
