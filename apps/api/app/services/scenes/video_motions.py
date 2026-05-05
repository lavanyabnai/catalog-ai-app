"""Video motion specs — used as prompt fragments for Kling/Veo generation."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VideoMotion:
    id: str
    display_name: str
    prompt_fragment: str


_MOTIONS: dict[str, VideoMotion] = {
    m.id: m
    for m in [
        VideoMotion(
            id="slow_turn_360",
            display_name="360° Turn",
            prompt_fragment="slowly rotating 360 degrees in place, studio white background, smooth movement",
        ),
        VideoMotion(
            id="confident_walk",
            display_name="Confident Walk",
            prompt_fragment="walking confidently toward camera, lifestyle setting, natural stride, dynamic energy",
        ),
        VideoMotion(
            id="product_pickup",
            display_name="Detail Close-up",
            prompt_fragment="close-up hand adjusting garment detail, soft focus background, artful gesture",
        ),
        VideoMotion(
            id="golden_hour_pose",
            display_name="Golden Hour Pose",
            prompt_fragment="outdoor lifestyle pose, golden hour light, gentle breeze, relaxed and natural",
        ),
    ]
}

ALL_MOTION_IDS: list[str] = list(_MOTIONS.keys())


def get_motion(motion_id: str) -> VideoMotion | None:
    return _MOTIONS.get(motion_id)


def get_all_motions() -> list[VideoMotion]:
    return list(_MOTIONS.values())
