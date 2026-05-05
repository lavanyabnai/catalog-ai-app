"""Plan builder — converts product + brand kit + personas into a list of GenerationShots.

A GenerationShot is one image generation job: one persona, one pose, one scene,
one primary aspect ratio. Aspect-ratio variants (crops) are produced in post-processing
by the Celery task — they are NOT separate jobs.

Default plan: 4 personas × 2 poses × 1 hero scene = 8 shots, plus 1 back shot = 9 total.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.models.brand_kits import BrandKit
    from app.models.catalog import Product
    from app.models.personas import ModelPersona

_DEFAULT_HERO_SCENE = "studio_white"
_DEFAULT_MAIN_POSES = ["front", "three_quarter"]
_DEFAULT_ASPECT_RATIOS = ["4:5", "1:1", "9:16"]
_MAX_PERSONAS = 4


@dataclass
class GenerationShot:
    """Spec for a single image generation job."""
    persona: dict[str, Any]
    pose: str
    scene: str
    primary_aspect_ratio: str  # generation aspect ratio; other ratios are Pillow-cropped


def _serialize_persona(persona: ModelPersona) -> dict[str, Any]:
    return {
        "id": str(persona.id),
        "display_name": persona.display_name,
        "body_type": persona.body_type,
        "ethnicity": persona.ethnicity,
        "age_range": persona.age_range,
        "height_cm": persona.height_cm,
        "gender_presentation": persona.gender_presentation,
        "hair": persona.hair,
    }


def pick_primary_aspect(required: list[str]) -> str:
    """Return the tallest (most portrait) aspect ratio to use for generation.

    We generate at the tallest ratio so all other required ratios can be
    obtained by cropping (no upscaling needed).
    """
    def w_over_h(s: str) -> float:
        w, h = map(int, s.split(":"))
        return w / h

    return min(required, key=w_over_h)


def build_plan(
    product: Product,
    personas: list[ModelPersona],
    brand_kit: BrandKit | None,
    overrides: list[dict[str, Any]] | None = None,
) -> list[GenerationShot]:
    """Build the list of GenerationShots for a product generation run.

    Args:
        product: The product being generated.
        personas: All personas available to the tenant (system + tenant's own).
        brand_kit: The product's brand kit, if any. Constrains scenes and personas.
        overrides: If provided, use these shot specs instead of building the default plan.
                   Each dict should have keys: persona (dict), pose, scene,
                   primary_aspect_ratio.

    Returns:
        A list of GenerationShot — one per image generation job.
    """
    required_ars: list[str] = (
        list(brand_kit.required_aspect_ratios)
        if brand_kit and brand_kit.required_aspect_ratios
        else _DEFAULT_ASPECT_RATIOS
    )
    primary_ar = pick_primary_aspect(required_ars)

    # --- Override path ---
    if overrides:
        shots: list[GenerationShot] = []
        for shot in overrides:
            persona_data = shot.get("persona")
            if not isinstance(persona_data, dict):
                continue
            shots.append(
                GenerationShot(
                    persona=persona_data,
                    pose=str(shot.get("pose", "front")),
                    scene=str(shot.get("scene", _DEFAULT_HERO_SCENE)),
                    primary_aspect_ratio=str(shot.get("primary_aspect_ratio", primary_ar)),
                )
            )
        if shots:
            return shots

    # --- Default plan ---

    # Filter personas by brand kit whitelist
    allowed_ids: set[str] | None = None
    if brand_kit and brand_kit.allowed_personas:
        sentinels = {str(x) for x in brand_kit.allowed_personas}
        if "diverse_default" not in sentinels:
            allowed_ids = sentinels

    if allowed_ids is not None:
        filtered = [p for p in personas if str(p.id) in allowed_ids]
    else:
        filtered = list(personas)

    # Fallback to all personas if the whitelist eliminated everything
    if not filtered:
        filtered = list(personas)

    selected = filtered[:_MAX_PERSONAS]

    if not selected:
        raise ValueError("No personas available — run make db-seed to add system personas")

    # Hero scene (first allowed scene, or default)
    hero_scene = _DEFAULT_HERO_SCENE
    if brand_kit and brand_kit.allowed_scenes:
        hero_scene = str(brand_kit.allowed_scenes[0])

    shots = []
    for persona in selected:
        for pose in _DEFAULT_MAIN_POSES:
            shots.append(
                GenerationShot(
                    persona=_serialize_persona(persona),
                    pose=pose,
                    scene=hero_scene,
                    primary_aspect_ratio=primary_ar,
                )
            )

    # Back shot with first persona (detail/construction shot)
    shots.append(
        GenerationShot(
            persona=_serialize_persona(selected[0]),
            pose="back",
            scene=hero_scene,
            primary_aspect_ratio=primary_ar,
        )
    )

    return shots  # default: 4×2 + 1 = 9 shots


def get_required_aspect_ratios(brand_kit: BrandKit | None) -> list[str]:
    """Return the required aspect ratios for a brand kit (or default)."""
    if brand_kit and brand_kit.required_aspect_ratios:
        return list(brand_kit.required_aspect_ratios)
    return _DEFAULT_ASPECT_RATIOS
