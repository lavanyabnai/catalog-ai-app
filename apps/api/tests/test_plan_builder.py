"""Unit tests for the plan builder, brand kit enforcement, and helper functions.

These tests are pure Python — no DB, no HTTP.
"""
from __future__ import annotations

import uuid
from io import BytesIO
from unittest.mock import MagicMock

import pytest
from PIL import Image

from app.services.plan_builder import (
    _DEFAULT_ASPECT_RATIOS,
    _DEFAULT_HERO_SCENE,
    build_plan,
    get_required_aspect_ratios,
    pick_primary_aspect,
)
from app.tasks.generate_image import _cm_to_imperial, _crop_to_aspect, _estimate_garment_size


# ---------------------------------------------------------------------------
# Test fixtures / builders
# ---------------------------------------------------------------------------

def _make_persona(
    display_name: str = "Test",
    body_type: str = "athletic",
    gender_presentation: str = "feminine",
    height_cm: int = 170,
    persona_id: str | None = None,
) -> MagicMock:
    p = MagicMock()
    p.id = uuid.UUID(persona_id) if persona_id else uuid.uuid4()
    p.display_name = display_name
    p.body_type = body_type
    p.ethnicity = "Test"
    p.age_range = "25-35"
    p.height_cm = height_cm
    p.gender_presentation = gender_presentation
    p.hair = "straight"
    p.system_managed = True
    p.tenant_id = None
    return p


def _make_brand_kit(
    allowed_scenes: list[str] | None = None,
    allowed_personas: list[str] | None = None,
    required_aspect_ratios: list[str] | None = None,
) -> MagicMock:
    bk = MagicMock()
    bk.allowed_scenes = allowed_scenes
    bk.allowed_personas = allowed_personas
    bk.required_aspect_ratios = required_aspect_ratios or ["4:5", "1:1", "9:16"]
    return bk


def _make_image_bytes(width: int, height: int) -> bytes:
    img = Image.new("RGB", (width, height), color=(128, 64, 32))
    buf = BytesIO()
    img.save(buf, format="WEBP")
    return buf.getvalue()


_FOUR_PERSONAS = [
    _make_persona("Aisha"),
    _make_persona("Sofia"),
    _make_persona("Emma"),
    _make_persona("Priya"),
]

_MOCK_PRODUCT = MagicMock()
_MOCK_PRODUCT.attributes = {}


# ---------------------------------------------------------------------------
# pick_primary_aspect
# ---------------------------------------------------------------------------

def test_pick_primary_aspect_returns_tallest() -> None:
    assert pick_primary_aspect(["4:5", "1:1", "9:16"]) == "9:16"


def test_pick_primary_aspect_single_item() -> None:
    assert pick_primary_aspect(["1:1"]) == "1:1"


def test_pick_primary_aspect_portrait_only() -> None:
    assert pick_primary_aspect(["4:5", "1:1"]) == "4:5"


# ---------------------------------------------------------------------------
# Default plan shape
# ---------------------------------------------------------------------------

def test_default_plan_produces_9_shots() -> None:
    shots = build_plan(_MOCK_PRODUCT, _FOUR_PERSONAS, brand_kit=None)
    assert len(shots) == 9


def test_default_plan_has_exactly_one_back_shot() -> None:
    shots = build_plan(_MOCK_PRODUCT, _FOUR_PERSONAS, brand_kit=None)
    assert len([s for s in shots if s.pose == "back"]) == 1


def test_default_plan_uses_studio_white_hero() -> None:
    shots = build_plan(_MOCK_PRODUCT, _FOUR_PERSONAS, brand_kit=None)
    assert all(s.scene == _DEFAULT_HERO_SCENE for s in shots)


def test_default_plan_primary_aspect_is_9_16() -> None:
    # Default required_ars = ["4:5","1:1","9:16"], tallest = "9:16"
    shots = build_plan(_MOCK_PRODUCT, _FOUR_PERSONAS, brand_kit=None)
    assert all(s.primary_aspect_ratio == "9:16" for s in shots)


def test_default_plan_uses_all_4_personas() -> None:
    shots = build_plan(_MOCK_PRODUCT, _FOUR_PERSONAS, brand_kit=None)
    persona_names = {s.persona["display_name"] for s in shots}
    assert persona_names == {"Aisha", "Sofia", "Emma", "Priya"}


# ---------------------------------------------------------------------------
# Brand kit — scene filtering
# ---------------------------------------------------------------------------

def test_brand_kit_overrides_hero_scene() -> None:
    bk = _make_brand_kit(allowed_scenes=["golden_hour_outdoor"])
    shots = build_plan(_MOCK_PRODUCT, _FOUR_PERSONAS, brand_kit=bk)
    assert all(s.scene == "golden_hour_outdoor" for s in shots)


def test_two_products_different_scenes_produce_different_distributions() -> None:
    """Brand kits with different scene lists produce distinct distributions."""
    bk_studio = _make_brand_kit(allowed_scenes=["studio_white"])
    bk_outdoor = _make_brand_kit(allowed_scenes=["golden_hour_outdoor"])

    shots_studio = build_plan(_MOCK_PRODUCT, _FOUR_PERSONAS, brand_kit=bk_studio)
    shots_outdoor = build_plan(_MOCK_PRODUCT, _FOUR_PERSONAS, brand_kit=bk_outdoor)

    scenes_studio = {s.scene for s in shots_studio}
    scenes_outdoor = {s.scene for s in shots_outdoor}

    assert scenes_studio == {"studio_white"}
    assert scenes_outdoor == {"golden_hour_outdoor"}
    assert scenes_studio.isdisjoint(scenes_outdoor)


# ---------------------------------------------------------------------------
# Brand kit — persona filtering
# ---------------------------------------------------------------------------

def test_brand_kit_filters_personas_to_whitelist() -> None:
    persona_a = _make_persona("A")
    persona_b = _make_persona("B")
    persona_c = _make_persona("C")

    bk = _make_brand_kit(allowed_personas=[str(persona_a.id), str(persona_b.id)])
    shots = build_plan(_MOCK_PRODUCT, [persona_a, persona_b, persona_c], brand_kit=bk)

    used_names = {s.persona["display_name"] for s in shots}
    assert "C" not in used_names
    assert used_names <= {"A", "B"}


def test_diverse_default_sentinel_uses_all_personas() -> None:
    bk = _make_brand_kit(allowed_personas=["diverse_default"])
    shots = build_plan(_MOCK_PRODUCT, _FOUR_PERSONAS, brand_kit=bk)
    assert {s.persona["display_name"] for s in shots} == {"Aisha", "Sofia", "Emma", "Priya"}


def test_two_products_different_personas_produce_different_distributions() -> None:
    """Brand kits with different persona whitelists → disjoint persona usage."""
    p1, p2 = _make_persona("Model1"), _make_persona("Model2")
    p3, p4 = _make_persona("Model3"), _make_persona("Model4")
    all_personas = [p1, p2, p3, p4]

    shots_a = build_plan(_MOCK_PRODUCT, all_personas, brand_kit=_make_brand_kit(allowed_personas=[str(p1.id), str(p2.id)]))
    shots_b = build_plan(_MOCK_PRODUCT, all_personas, brand_kit=_make_brand_kit(allowed_personas=[str(p3.id), str(p4.id)]))

    names_a = {s.persona["display_name"] for s in shots_a}
    names_b = {s.persona["display_name"] for s in shots_b}

    assert names_a == {"Model1", "Model2"}
    assert names_b == {"Model3", "Model4"}
    assert names_a.isdisjoint(names_b)


# ---------------------------------------------------------------------------
# Brand kit — required aspect ratios
# ---------------------------------------------------------------------------

def test_brand_kit_aspect_ratios_affect_primary_ar() -> None:
    bk = _make_brand_kit(required_aspect_ratios=["4:5", "1:1"])
    shots = build_plan(_MOCK_PRODUCT, _FOUR_PERSONAS, brand_kit=bk)
    # tallest of ["4:5","1:1"] is "4:5"
    assert all(s.primary_aspect_ratio == "4:5" for s in shots)


def test_get_required_aspect_ratios_no_brand_kit() -> None:
    assert get_required_aspect_ratios(None) == _DEFAULT_ASPECT_RATIOS


def test_get_required_aspect_ratios_from_brand_kit() -> None:
    bk = _make_brand_kit(required_aspect_ratios=["4:5"])
    assert get_required_aspect_ratios(bk) == ["4:5"]


# ---------------------------------------------------------------------------
# Override path — custom persona support
# ---------------------------------------------------------------------------

def test_overrides_bypass_default_plan() -> None:
    custom_persona = {
        "id": str(uuid.uuid4()), "display_name": "Custom",
        "body_type": "slim", "ethnicity": "Any", "age_range": "20-30",
        "height_cm": 165, "gender_presentation": "feminine", "hair": "short",
    }
    overrides = [
        {"persona": custom_persona, "pose": "sitting",
         "scene": "coastal_cafe", "primary_aspect_ratio": "4:5"},
    ]
    shots = build_plan(_MOCK_PRODUCT, _FOUR_PERSONAS, brand_kit=None, overrides=overrides)
    assert len(shots) == 1
    assert shots[0].pose == "sitting"
    assert shots[0].scene == "coastal_cafe"
    assert shots[0].persona["display_name"] == "Custom"


def test_custom_tenant_persona_usable_in_plan_override() -> None:
    """A tenant-created persona (not system_managed) can drive a plan via overrides."""
    tenant_persona = {
        "id": str(uuid.uuid4()), "display_name": "TenantModel",
        "body_type": "hourglass", "ethnicity": "Mixed", "age_range": "28-38",
        "height_cm": 173, "gender_presentation": "feminine", "hair": "curly medium",
    }
    overrides = [
        {"persona": tenant_persona, "pose": "front", "scene": "urban_loft_interior"},
        {"persona": tenant_persona, "pose": "three_quarter", "scene": "urban_loft_interior"},
    ]
    shots = build_plan(_MOCK_PRODUCT, _FOUR_PERSONAS, brand_kit=None, overrides=overrides)
    assert len(shots) == 2
    assert all(s.persona["display_name"] == "TenantModel" for s in shots)
    assert all(s.scene == "urban_loft_interior" for s in shots)


# ---------------------------------------------------------------------------
# Model spec helpers
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cm,expected", [
    (152, "5'0\""),
    (160, "5'3\""),
    (162, "5'4\""),
    (170, "5'7\""),
    (178, "5'10\""),
    (182, "6'0\""),
    (185, "6'1\""),
    (190, "6'3\""),
])
def test_cm_to_imperial(cm: int, expected: str) -> None:
    assert _cm_to_imperial(cm) == expected


def test_estimate_garment_size_uses_size_range_attribute() -> None:
    assert _estimate_garment_size({"body_type": "slim"}, {"size_range": "XS-XL"}) == "XS"


def test_estimate_garment_size_single_value_range() -> None:
    assert _estimate_garment_size({"body_type": "slim"}, {"size_range": "M"}) == "M"


def test_estimate_garment_size_falls_back_to_body_type() -> None:
    assert _estimate_garment_size({"body_type": "curvy"}, {}) == "L"


def test_estimate_garment_size_unknown_body_type_defaults_m() -> None:
    assert _estimate_garment_size({"body_type": "zzz"}, {}) == "M"


# ---------------------------------------------------------------------------
# Aspect-ratio crop
# ---------------------------------------------------------------------------

def test_crop_9_16_to_4_5_correct_dimensions() -> None:
    """Cropping a 576×1024 (9:16) image to 4:5 should give 576×720."""
    img_bytes = _make_image_bytes(576, 1024)
    cropped = _crop_to_aspect(img_bytes, "4:5")
    with Image.open(BytesIO(cropped)) as img:
        w, h = img.size
    assert w == 576
    assert h == 720


def test_crop_9_16_to_1_1_correct_dimensions() -> None:
    """Cropping 576×1024 to 1:1 should give 576×576."""
    img_bytes = _make_image_bytes(576, 1024)
    cropped = _crop_to_aspect(img_bytes, "1:1")
    with Image.open(BytesIO(cropped)) as img:
        w, h = img.size
    assert w == 576
    assert h == 576


def test_crop_same_ratio_returns_same_size() -> None:
    """Cropping to the same aspect ratio should return the same dimensions."""
    img_bytes = _make_image_bytes(800, 1000)
    cropped = _crop_to_aspect(img_bytes, "4:5")  # 800/1000 = 0.8 = 4/5
    with Image.open(BytesIO(cropped)) as img:
        w, h = img.size
    assert w == 800
    assert h == 1000


def test_crop_4_5_to_1_1() -> None:
    """Cropping 800×1000 (4:5) to 1:1 should give 800×800."""
    img_bytes = _make_image_bytes(800, 1000)
    cropped = _crop_to_aspect(img_bytes, "1:1")
    with Image.open(BytesIO(cropped)) as img:
        w, h = img.size
    assert w == 800
    assert h == 800
