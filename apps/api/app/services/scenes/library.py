"""Scene library — static data, not code.

Each scene defines a visual setting for on-model photography.
Prompt fragments are inserted directly into FLUX prompts by the prompt builder.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SceneSpec:
    id: str
    display_name: str
    prompt_fragment: str
    negative_prompt_fragment: str
    compatible_garment_categories: list[str]
    lighting_notes: str


_SCENES: list[SceneSpec] = [
    SceneSpec(
        id="studio_white",
        display_name="Studio White",
        prompt_fragment=(
            "in a professional fashion studio, pure white seamless paper backdrop, "
            "soft diffused studio lighting, no shadows, clean white floor"
        ),
        negative_prompt_fragment="outdoor, nature, window, colored background, texture",
        compatible_garment_categories=[
            "women-tshirts", "women-blouses", "women-dresses", "men-tshirts",
        ],
        lighting_notes="Soft box from above-front; no hard shadows.",
    ),
    SceneSpec(
        id="studio_neutral",
        display_name="Studio Neutral",
        prompt_fragment=(
            "in a professional fashion studio, warm neutral grey seamless backdrop, "
            "soft directional key light with subtle fill, editorial fashion look"
        ),
        negative_prompt_fragment="white background, outdoor, color cast, bright colors",
        compatible_garment_categories=[
            "women-tshirts", "women-blouses", "women-dresses", "men-tshirts",
        ],
        lighting_notes="Directional key light from 45° with 2:1 fill ratio.",
    ),
    SceneSpec(
        id="coastal_cafe",
        display_name="Coastal Café",
        prompt_fragment=(
            "at a bright coastal café with white-painted walls and Mediterranean blue accents, "
            "soft natural morning light, wicker furniture visible in background, "
            "light airy atmosphere, warm and inviting"
        ),
        negative_prompt_fragment="dark interior, night scene, urban grit, industrial, city streets",
        compatible_garment_categories=[
            "women-tshirts", "women-blouses", "women-dresses",
        ],
        lighting_notes="Soft diffused natural light from nearby window or open terrace.",
    ),
    SceneSpec(
        id="sunlit_street",
        display_name="Sunlit Street",
        prompt_fragment=(
            "on a sun-drenched city sidewalk, clean urban street, soft natural daylight, "
            "blurred city background with gentle bokeh, editorial outdoor fashion photography, "
            "cosmopolitan urban setting"
        ),
        negative_prompt_fragment="studio backdrop, indoor, night, rain, dark alley",
        compatible_garment_categories=[
            "women-tshirts", "women-blouses", "women-dresses", "men-tshirts",
        ],
        lighting_notes="Overcast or gentle directional sunlight. Avoid harsh midday shadows.",
    ),
    SceneSpec(
        id="golden_hour_outdoor",
        display_name="Golden Hour Outdoor",
        prompt_fragment=(
            "in a park or open outdoor setting during golden hour, warm golden backlight, "
            "soft rim lighting on the model, romantic warm amber tones, "
            "luxury fashion editorial style, shallow depth of field"
        ),
        negative_prompt_fragment=(
            "studio, indoor, harsh midday light, overcast grey sky, cold tones"
        ),
        compatible_garment_categories=[
            "women-tshirts", "women-blouses", "women-dresses", "men-tshirts",
        ],
        lighting_notes="Backlit golden hour with reflector fill. Warm color grade.",
    ),
    SceneSpec(
        id="urban_loft_interior",
        display_name="Urban Loft Interior",
        prompt_fragment=(
            "inside a modern urban loft with exposed brick wall and large industrial windows, "
            "soft diffused natural window light, minimalist contemporary interior, "
            "editorial fashion photography, clean sophisticated look"
        ),
        negative_prompt_fragment="outdoor, beach, busy background, studio white backdrop",
        compatible_garment_categories=[
            "women-tshirts", "women-blouses", "women-dresses", "men-tshirts",
        ],
        lighting_notes="Window light from one side with a subtle bounce fill.",
    ),
]

_SCENE_INDEX: dict[str, SceneSpec] = {s.id: s for s in _SCENES}

ALL_SCENE_IDS: list[str] = [s.id for s in _SCENES]


def get_scene(scene_id: str) -> SceneSpec | None:
    return _SCENE_INDEX.get(scene_id)


def get_all_scenes() -> list[SceneSpec]:
    return list(_SCENES)
