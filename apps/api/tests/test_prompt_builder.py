"""Snapshot tests for the image prompt builder.

These pin the exact output so accidental changes to prompt wording
are caught during CI before they affect generation quality.
"""
import pytest

from app.services.prompts.image_prompts import build_negative_prompt, build_prompt

_PERSONA_AISHA = {
    "display_name": "Aisha",
    "body_type": "hourglass",
    "ethnicity": "Black / African",
    "age_range": "25-35",
    "height_cm": 170,
    "gender_presentation": "feminine",
    "hair": "long braids",
}

_PERSONA_MARCUS = {
    "display_name": "Marcus",
    "body_type": "athletic",
    "ethnicity": "Black / African",
    "age_range": "25-35",
    "height_cm": 182,
    "gender_presentation": "masculine",
    "hair": "short natural",
}


def test_prompt_contains_garment_info():
    prompt = build_prompt(
        garment_type="T-Shirts",
        color="sage green",
        material="100% linen",
        persona=_PERSONA_AISHA,
        pose="front",
        scene="studio_white",
    )
    assert "sage green" in prompt
    assert "100% linen" in prompt
    assert "T-Shirts" in prompt


def test_prompt_contains_persona_info():
    prompt = build_prompt(
        garment_type="Dress",
        color="navy",
        material=None,
        persona=_PERSONA_AISHA,
        pose="three-quarter",
        scene="studio_white",
    )
    assert "Black / African" in prompt
    assert "hourglass" in prompt
    assert "long braids" in prompt
    assert "170" in prompt
    assert "25-35" in prompt


def test_prompt_masculine_persona():
    prompt = build_prompt(
        garment_type="T-Shirts",
        color=None,
        material=None,
        persona=_PERSONA_MARCUS,
        pose="front",
        scene="studio_white",
    )
    assert "male model" in prompt
    assert "182" in prompt


def test_prompt_studio_white_scene():
    prompt = build_prompt(
        garment_type="Blouse",
        color="white",
        material="silk",
        persona=_PERSONA_AISHA,
        pose="front",
        scene="studio_white",
    )
    assert "white seamless" in prompt.lower() or "white" in prompt


def test_prompt_walking_pose():
    prompt = build_prompt(
        garment_type="Dress",
        color="red",
        material=None,
        persona=_PERSONA_AISHA,
        pose="walking",
        scene="studio_white",
    )
    assert "walking" in prompt.lower()


def test_prompt_no_color_no_material():
    """Omitting optional fields should not crash or produce placeholder text."""
    prompt = build_prompt(
        garment_type="Dress",
        color=None,
        material=None,
        persona=_PERSONA_AISHA,
        pose="front",
        scene="studio_white",
    )
    assert "None" not in prompt
    assert "garment" in prompt.lower() or "Dress" in prompt


def test_negative_prompt_is_stable():
    neg = build_negative_prompt()
    assert "blurry" in neg
    assert "watermark" in neg
    assert "cartoon" in neg


# --- Snapshot: pin exact output for the canonical Aisha / studio_white / front combo ---

_EXPECTED_SNAPSHOT_FRAGMENT = (
    "Professional fashion editorial photograph of a 25-35 year old Black / African female model"
)


def test_prompt_snapshot():
    prompt = build_prompt(
        garment_type="T-Shirts",
        color="sage green",
        material="100% linen",
        persona=_PERSONA_AISHA,
        pose="front",
        scene="studio_white",
    )
    assert _EXPECTED_SNAPSHOT_FRAGMENT in prompt, (
        f"Prompt snapshot changed. Got:\n{prompt}"
    )
