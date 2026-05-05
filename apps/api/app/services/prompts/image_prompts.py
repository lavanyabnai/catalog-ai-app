"""Prompt construction for FLUX image-to-image fashion generation.

All prompt-engineering logic is isolated here so it can be unit-tested
independently of the provider HTTP layer.
"""
from __future__ import annotations

from typing import Any

from app.services.poses.library import get_pose
from app.services.scenes.library import get_scene

_DEFAULT_SCENE_FRAGMENT = (
    "in a professional fashion studio, white seamless backdrop, soft diffused lighting"
)
_DEFAULT_POSE_FRAGMENT = "standing facing directly forward, arms relaxed at sides"


def build_prompt(
    *,
    garment_type: str,
    color: str | None,
    material: str | None,
    persona: dict[str, Any],
    pose: str = "front",
    scene: str = "studio_white",
    extra_attributes: dict[str, Any] | None = None,
) -> str:
    """Return the full text prompt for FLUX img2img fashion generation."""

    # --- Garment description ---
    garment_parts: list[str] = []
    if color:
        garment_parts.append(color)
    if material:
        garment_parts.append(material)
    garment_parts.append(garment_type)
    garment_desc = " ".join(garment_parts)

    # --- Persona description ---
    gender = persona.get("gender_presentation", "feminine")
    ethnicity = persona.get("ethnicity", "")
    body_type = persona.get("body_type", "")
    age_range = persona.get("age_range", "")
    height_cm = persona.get("height_cm", "")
    hair = persona.get("hair", "")

    model_parts: list[str] = []
    if age_range:
        model_parts.append(f"{age_range} year old")
    if ethnicity:
        model_parts.append(ethnicity)
    if gender in ("masculine", "gender-neutral"):
        model_parts.append("male model" if gender == "masculine" else "model")
    else:
        model_parts.append("female model")
    if body_type:
        model_parts.append(f"with {body_type} build")
    if height_cm:
        model_parts.append(f"{height_cm}cm tall")
    if hair:
        model_parts.append(f"with {hair} hair")
    model_desc = " ".join(model_parts)

    # --- Pose (library-backed) ---
    pose_spec = get_pose(pose)
    pose_desc = pose_spec.prompt_fragment if pose_spec else _DEFAULT_POSE_FRAGMENT

    # --- Scene (library-backed) ---
    scene_spec = get_scene(scene)
    scene_desc = scene_spec.prompt_fragment if scene_spec else _DEFAULT_SCENE_FRAGMENT

    prompt = (
        f"Professional fashion editorial photograph of a {model_desc}, "
        f"wearing a {garment_desc}. "
        f"The model is {pose_desc}. "
        f"Setting: {scene_desc}. "
        "Photorealistic, high resolution, sharp focus, commercial fashion photography quality, "
        "full body shot showing the complete garment."
    )
    return prompt


def build_negative_prompt(scene: str = "") -> str:
    """Return the negative prompt, optionally appending scene-specific exclusions."""
    base = (
        "blurry, low quality, distorted, deformed, ugly, bad anatomy, "
        "extra limbs, missing limbs, watermark, text, logo, cropped, "
        "out of frame, duplicate, cartoon, anime, illustration"
    )
    scene_spec = get_scene(scene)
    if scene_spec and scene_spec.negative_prompt_fragment:
        return f"{base}, {scene_spec.negative_prompt_fragment}"
    return base
