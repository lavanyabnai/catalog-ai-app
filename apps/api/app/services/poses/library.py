"""Pose library — static data, not code.

Each pose defines a body position for the model in on-model photography.
Prompt fragments are inserted directly into FLUX prompts by the prompt builder.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PoseSpec:
    id: str
    display_name: str
    prompt_fragment: str


_POSES: list[PoseSpec] = [
    PoseSpec(
        id="front",
        display_name="Front",
        prompt_fragment=(
            "standing facing directly forward, arms relaxed at sides, "
            "full body visible, confident neutral expression"
        ),
    ),
    PoseSpec(
        id="three_quarter",
        display_name="Three-Quarter",
        prompt_fragment=(
            "standing at a three-quarter angle turned slightly to the side, "
            "weight shifted naturally to one hip, elegant relaxed stance"
        ),
    ),
    PoseSpec(
        id="back",
        display_name="Back",
        prompt_fragment=(
            "standing with back to camera, head slightly turned over one shoulder, "
            "showcasing the back of the garment, hair and neckline visible"
        ),
    ),
    PoseSpec(
        id="walking",
        display_name="Walking",
        prompt_fragment=(
            "mid-stride walking pose, natural movement, "
            "hair and garment gently moving, dynamic editorial energy"
        ),
    ),
    PoseSpec(
        id="sitting",
        display_name="Sitting",
        prompt_fragment=(
            "sitting naturally on a surface, relaxed and confident posture, "
            "garment draping beautifully, casual yet polished"
        ),
    ),
    PoseSpec(
        id="hands_in_pockets",
        display_name="Hands in Pockets",
        prompt_fragment=(
            "standing casually with both hands tucked in pockets, "
            "relaxed confident pose, slight weight shift to one side"
        ),
    ),
    PoseSpec(
        id="looking_away",
        display_name="Looking Away",
        prompt_fragment=(
            "standing while looking off to the side into the distance, "
            "editorial profile angle, contemplative thoughtful expression, "
            "strong jawline and posture"
        ),
    ),
]

_POSE_INDEX: dict[str, PoseSpec] = {p.id: p for p in _POSES}

ALL_POSE_IDS: list[str] = [p.id for p in _POSES]


def get_pose(pose_id: str) -> PoseSpec | None:
    return _POSE_INDEX.get(pose_id)


def get_all_poses() -> list[PoseSpec]:
    return list(_POSES)
