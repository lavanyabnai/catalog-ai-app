"""Seed script — run via `make db-seed` (uv run python -m app.seed).

Populates:
- Global category tree (6 categories)
- Attribute definitions per leaf category (3-4 each)
- 8 default system-managed ModelPersonas
"""
import os
import uuid

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.models import (
    AttributeDefinition,
    Base,  # noqa: F401 — ensures mapper is ready
    Category,
    ModelPersona,
)
from app.models.enums import AttributeValueType

_db_url = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/catalog_ai",
).replace("postgresql+asyncpg://", "postgresql://")

engine = create_engine(_db_url, future=True)


def _upsert_category(
    session: Session,
    slug: str,
    display_name: str,
    path: str,
    parent_id: uuid.UUID | None,
) -> Category:
    existing = session.query(Category).filter_by(slug=slug, tenant_id=None).first()
    if existing:
        return existing
    cat = Category(
        slug=slug,
        display_name=display_name,
        path=path,
        parent_id=parent_id,
        tenant_id=None,
    )
    session.add(cat)
    session.flush()
    return cat


def _upsert_attr(
    session: Session,
    category_id: uuid.UUID,
    key: str,
    display_name: str,
    value_type: AttributeValueType,
    allowed_values: list[str] | None = None,
    is_required: bool = False,
) -> None:
    existing = session.query(AttributeDefinition).filter_by(category_id=category_id, key=key).first()
    if existing:
        return
    session.add(
        AttributeDefinition(
            category_id=category_id,
            key=key,
            display_name=display_name,
            value_type=value_type,
            is_required=is_required,
            allowed_values=allowed_values,
        )
    )


def _upsert_persona(session: Session, **kwargs: object) -> None:
    existing = session.query(ModelPersona).filter_by(display_name=kwargs["display_name"], tenant_id=None).first()
    if existing:
        return
    session.add(ModelPersona(**kwargs))


def seed(session: Session) -> None:
    # Disable RLS for seed (we're running as superuser; RLS bypasses automatically)
    session.execute(text("SET app.current_tenant_id = '00000000-0000-0000-0000-000000000000'"))

    # ------------------------------------------------------------------
    # Category tree
    # ------------------------------------------------------------------
    #   Apparel
    #   └── Women's Tops
    #       ├── T-Shirts
    #       └── Blouses
    #   └── Women's Dresses
    #   └── Men's T-Shirts
    # ------------------------------------------------------------------
    apparel = _upsert_category(session, "apparel", "Apparel", "apparel", None)
    women_tops = _upsert_category(session, "women-tops", "Women's Tops", "apparel.women-tops", apparel.id)
    _upsert_category(session, "women-tshirts", "T-Shirts", "apparel.women-tops.women-tshirts", women_tops.id)
    _upsert_category(session, "women-blouses", "Blouses", "apparel.women-tops.women-blouses", women_tops.id)
    _upsert_category(session, "women-dresses", "Women's Dresses", "apparel.women-dresses", apparel.id)
    _upsert_category(session, "men-tshirts", "Men's T-Shirts", "apparel.men-tshirts", apparel.id)
    session.flush()

    # ------------------------------------------------------------------
    # Attribute definitions for leaf categories
    # ------------------------------------------------------------------
    def _get(slug: str) -> Category:
        cat = session.query(Category).filter_by(slug=slug, tenant_id=None).one()
        return cat

    # Women's T-Shirts
    tshirt_id = _get("women-tshirts").id
    _upsert_attr(session, tshirt_id, "neckline", "Neckline", AttributeValueType.enum,
                 ["crew", "v-neck", "scoop", "boat"])
    _upsert_attr(session, tshirt_id, "sleeve_length", "Sleeve Length", AttributeValueType.enum,
                 ["short", "long", "sleeveless"])
    _upsert_attr(session, tshirt_id, "fit", "Fit", AttributeValueType.enum,
                 ["slim", "regular", "oversized"])

    # Blouses
    blouse_id = _get("women-blouses").id
    _upsert_attr(session, blouse_id, "collar_type", "Collar Type", AttributeValueType.enum,
                 ["button-down", "mandarin", "peter-pan", "spread"])
    _upsert_attr(session, blouse_id, "sleeve_length", "Sleeve Length", AttributeValueType.enum,
                 ["short", "long", "3/4", "sleeveless"])
    _upsert_attr(session, blouse_id, "fit", "Fit", AttributeValueType.enum,
                 ["slim", "regular", "relaxed"])

    # Women's Dresses
    dress_id = _get("women-dresses").id
    _upsert_attr(session, dress_id, "dress_length", "Dress Length", AttributeValueType.enum,
                 ["mini", "midi", "maxi"])
    _upsert_attr(session, dress_id, "neckline", "Neckline", AttributeValueType.enum,
                 ["crew", "v-neck", "off-shoulder", "square"])
    _upsert_attr(session, dress_id, "silhouette", "Silhouette", AttributeValueType.enum,
                 ["a-line", "bodycon", "shift", "wrap", "shirt"])

    # Men's T-Shirts
    mens_tshirt_id = _get("men-tshirts").id
    _upsert_attr(session, mens_tshirt_id, "neckline", "Neckline", AttributeValueType.enum,
                 ["crew", "v-neck", "polo"])
    _upsert_attr(session, mens_tshirt_id, "sleeve_length", "Sleeve Length", AttributeValueType.enum,
                 ["short", "long", "sleeveless"])
    _upsert_attr(session, mens_tshirt_id, "fit", "Fit", AttributeValueType.enum,
                 ["slim", "regular", "loose"])

    # ------------------------------------------------------------------
    # Model personas — 8 diverse system-managed personas
    # ------------------------------------------------------------------
    personas = [
        dict(display_name="Aisha", body_type="hourglass", ethnicity="Black / African",
             age_range="25-35", height_cm=170, gender_presentation="feminine",
             hair="long braids", system_managed=True, tenant_id=None),
        dict(display_name="Sofia", body_type="athletic", ethnicity="Latina / Hispanic",
             age_range="22-30", height_cm=165, gender_presentation="feminine",
             hair="wavy dark", system_managed=True, tenant_id=None),
        dict(display_name="Emma", body_type="petite", ethnicity="White / European",
             age_range="20-28", height_cm=162, gender_presentation="feminine",
             hair="straight blonde", system_managed=True, tenant_id=None),
        dict(display_name="Priya", body_type="curvy", ethnicity="South Asian",
             age_range="25-35", height_cm=168, gender_presentation="feminine",
             hair="long dark straight", system_managed=True, tenant_id=None),
        dict(display_name="Zara", body_type="tall-slim", ethnicity="Middle Eastern",
             age_range="22-32", height_cm=175, gender_presentation="feminine",
             hair="hijab (neutral wrap)", system_managed=True, tenant_id=None),
        dict(display_name="Marcus", body_type="athletic", ethnicity="Black / African",
             age_range="25-35", height_cm=182, gender_presentation="masculine",
             hair="short natural", system_managed=True, tenant_id=None),
        dict(display_name="James", body_type="slim", ethnicity="White / European",
             age_range="22-30", height_cm=178, gender_presentation="masculine",
             hair="short brown", system_managed=True, tenant_id=None),
        dict(display_name="Kai", body_type="slim", ethnicity="East Asian",
             age_range="20-28", height_cm=172, gender_presentation="gender-neutral",
             hair="short textured", system_managed=True, tenant_id=None),
    ]
    for p in personas:
        _upsert_persona(session, **p)

    session.commit()
    print("Seed complete.")


if __name__ == "__main__":
    with Session(engine) as session:
        seed(session)
