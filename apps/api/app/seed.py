"""Seed script — run via `make db-seed` (uv run python -m app.seed).

Populates:
- Global category tree (6 categories)
- Attribute definitions per leaf category (3-4 each)
- 8 default system-managed ModelPersonas
"""
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")
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
if "neon.tech" in _db_url and "sslmode" not in _db_url:
    _db_url += ("&" if "?" in _db_url else "?") + "sslmode=require"

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
    #   Western Wear
    #   └── Women's Tops
    #       ├── T-Shirts & Tops
    #       └── Blouses & Shirts
    #   └── Women's Dresses & Skirts
    #       ├── Dresses
    #       └── Skirts
    #   └── Women's Bottoms
    #       ├── Jeans
    #       └── Trousers & Palazzos
    #   └── Men's Tops
    #       ├── T-Shirts
    #       └── Shirts
    #   └── Men's Bottoms
    #       ├── Jeans
    #       └── Trousers & Chinos
    #   └── Outerwear
    #       ├── Women's Jackets & Coats
    #       └── Men's Jackets & Coats
    #
    #   Indian Ethnic — Women
    #   ├── Kurtas & Kurtis
    #   ├── Sarees
    #   ├── Lehengas
    #   ├── Salwar Kameez
    #   ├── Anarkali Suits
    #   ├── Coord Sets
    #   └── Dupattas & Stoles
    #
    #   Indian Ethnic — Men
    #   ├── Kurtas & Sherwanis
    #   ├── Nehru Jackets
    #   └── Dhotis & Lungis
    # ------------------------------------------------------------------

    # ── Western Wear ────────────────────────────────────────────────
    western = _upsert_category(session, "western", "Western Wear", "western", None)

    w_tops = _upsert_category(session, "women-tops", "Women's Tops", "western.women-tops", western.id)
    _upsert_category(session, "women-tshirts", "T-Shirts & Tops", "western.women-tops.women-tshirts", w_tops.id)
    _upsert_category(session, "women-blouses", "Blouses & Shirts", "western.women-tops.women-blouses", w_tops.id)

    w_dresses = _upsert_category(session, "women-dresses-skirts", "Women's Dresses & Skirts", "western.women-dresses-skirts", western.id)
    _upsert_category(session, "women-dresses", "Dresses", "western.women-dresses-skirts.women-dresses", w_dresses.id)
    _upsert_category(session, "women-skirts", "Skirts", "western.women-dresses-skirts.women-skirts", w_dresses.id)

    w_bottoms = _upsert_category(session, "women-bottoms", "Women's Bottoms", "western.women-bottoms", western.id)
    _upsert_category(session, "women-jeans", "Jeans", "western.women-bottoms.women-jeans", w_bottoms.id)
    _upsert_category(session, "women-trousers", "Trousers & Palazzos", "western.women-bottoms.women-trousers", w_bottoms.id)

    m_tops = _upsert_category(session, "men-tops", "Men's Tops", "western.men-tops", western.id)
    _upsert_category(session, "men-tshirts", "T-Shirts", "western.men-tops.men-tshirts", m_tops.id)
    _upsert_category(session, "men-shirts", "Shirts", "western.men-tops.men-shirts", m_tops.id)

    m_bottoms = _upsert_category(session, "men-bottoms", "Men's Bottoms", "western.men-bottoms", western.id)
    _upsert_category(session, "men-jeans", "Jeans", "western.men-bottoms.men-jeans", m_bottoms.id)
    _upsert_category(session, "men-trousers", "Trousers & Chinos", "western.men-bottoms.men-trousers", m_bottoms.id)

    outerwear = _upsert_category(session, "outerwear", "Outerwear", "western.outerwear", western.id)
    _upsert_category(session, "women-jackets", "Women's Jackets & Coats", "western.outerwear.women-jackets", outerwear.id)
    _upsert_category(session, "men-jackets", "Men's Jackets & Coats", "western.outerwear.men-jackets", outerwear.id)

    # ── Indian Ethnic — Women ────────────────────────────────────────
    ethnic_w = _upsert_category(session, "ethnic-women", "Indian Ethnic — Women", "ethnic-women", None)
    _upsert_category(session, "kurtas-kurtis", "Kurtas & Kurtis", "ethnic-women.kurtas-kurtis", ethnic_w.id)
    _upsert_category(session, "sarees", "Sarees", "ethnic-women.sarees", ethnic_w.id)
    _upsert_category(session, "lehengas", "Lehengas", "ethnic-women.lehengas", ethnic_w.id)
    _upsert_category(session, "salwar-kameez", "Salwar Kameez", "ethnic-women.salwar-kameez", ethnic_w.id)
    _upsert_category(session, "anarkali-suits", "Anarkali Suits", "ethnic-women.anarkali-suits", ethnic_w.id)
    _upsert_category(session, "ethnic-coord-sets", "Coord Sets", "ethnic-women.ethnic-coord-sets", ethnic_w.id)
    _upsert_category(session, "dupattas-stoles", "Dupattas & Stoles", "ethnic-women.dupattas-stoles", ethnic_w.id)

    # ── Indian Ethnic — Men ──────────────────────────────────────────
    ethnic_m = _upsert_category(session, "ethnic-men", "Indian Ethnic — Men", "ethnic-men", None)
    _upsert_category(session, "kurtas-sherwanis", "Kurtas & Sherwanis", "ethnic-men.kurtas-sherwanis", ethnic_m.id)
    _upsert_category(session, "nehru-jackets", "Nehru Jackets", "ethnic-men.nehru-jackets", ethnic_m.id)
    _upsert_category(session, "dhotis-lungis", "Dhotis & Lungis", "ethnic-men.dhotis-lungis", ethnic_m.id)

    session.flush()

    # ------------------------------------------------------------------
    # Attribute definitions for leaf categories
    # ------------------------------------------------------------------
    def _get(slug: str) -> Category:
        cat = session.query(Category).filter_by(slug=slug, tenant_id=None).first()
        return cat

    # T-Shirts & Tops
    tshirt_id = _get("women-tshirts").id
    _upsert_attr(session, tshirt_id, "neckline", "Neckline", AttributeValueType.enum,
                 ["crew", "v-neck", "scoop", "boat", "off-shoulder"])
    _upsert_attr(session, tshirt_id, "sleeve_length", "Sleeve Length", AttributeValueType.enum,
                 ["short", "long", "sleeveless", "3/4"])
    _upsert_attr(session, tshirt_id, "fit", "Fit", AttributeValueType.enum,
                 ["slim", "regular", "oversized", "crop"])

    # Blouses & Shirts
    blouse_id = _get("women-blouses").id
    _upsert_attr(session, blouse_id, "collar_type", "Collar Type", AttributeValueType.enum,
                 ["button-down", "mandarin", "peter-pan", "spread", "band"])
    _upsert_attr(session, blouse_id, "sleeve_length", "Sleeve Length", AttributeValueType.enum,
                 ["short", "long", "3/4", "sleeveless"])
    _upsert_attr(session, blouse_id, "fit", "Fit", AttributeValueType.enum,
                 ["slim", "regular", "relaxed"])

    # Dresses
    dress_id = _get("women-dresses").id
    _upsert_attr(session, dress_id, "dress_length", "Dress Length", AttributeValueType.enum,
                 ["mini", "midi", "maxi"])
    _upsert_attr(session, dress_id, "neckline", "Neckline", AttributeValueType.enum,
                 ["crew", "v-neck", "off-shoulder", "square", "halter"])
    _upsert_attr(session, dress_id, "silhouette", "Silhouette", AttributeValueType.enum,
                 ["a-line", "bodycon", "shift", "wrap", "shirt", "tiered"])

    # Skirts
    skirt_id = _get("women-skirts").id
    _upsert_attr(session, skirt_id, "skirt_length", "Skirt Length", AttributeValueType.enum,
                 ["mini", "midi", "maxi"])
    _upsert_attr(session, skirt_id, "silhouette", "Silhouette", AttributeValueType.enum,
                 ["a-line", "pencil", "tiered", "wrap", "pleated"])

    # Women's Jeans
    wjeans_id = _get("women-jeans").id
    _upsert_attr(session, wjeans_id, "fit", "Fit", AttributeValueType.enum,
                 ["skinny", "slim", "straight", "wide-leg", "flare", "mom"])
    _upsert_attr(session, wjeans_id, "rise", "Rise", AttributeValueType.enum,
                 ["low", "mid", "high"])

    # Women's Trousers
    wtrousers_id = _get("women-trousers").id
    _upsert_attr(session, wtrousers_id, "fit", "Fit", AttributeValueType.enum,
                 ["slim", "straight", "wide-leg", "palazzo", "flare"])
    _upsert_attr(session, wtrousers_id, "length", "Length", AttributeValueType.enum,
                 ["full", "ankle", "cropped"])

    # Men's T-Shirts
    mens_tshirt_id = _get("men-tshirts").id
    _upsert_attr(session, mens_tshirt_id, "neckline", "Neckline", AttributeValueType.enum,
                 ["crew", "v-neck", "polo", "henley"])
    _upsert_attr(session, mens_tshirt_id, "sleeve_length", "Sleeve Length", AttributeValueType.enum,
                 ["short", "long", "sleeveless"])
    _upsert_attr(session, mens_tshirt_id, "fit", "Fit", AttributeValueType.enum,
                 ["slim", "regular", "loose", "oversized"])

    # Men's Shirts
    mens_shirt_id = _get("men-shirts").id
    _upsert_attr(session, mens_shirt_id, "collar_type", "Collar Type", AttributeValueType.enum,
                 ["spread", "button-down", "band", "mandarin"])
    _upsert_attr(session, mens_shirt_id, "sleeve_length", "Sleeve Length", AttributeValueType.enum,
                 ["short", "long", "rolled"])
    _upsert_attr(session, mens_shirt_id, "fit", "Fit", AttributeValueType.enum,
                 ["slim", "regular", "relaxed"])

    # Men's Jeans
    mjeans_id = _get("men-jeans").id
    _upsert_attr(session, mjeans_id, "fit", "Fit", AttributeValueType.enum,
                 ["skinny", "slim", "straight", "relaxed", "wide-leg"])
    _upsert_attr(session, mjeans_id, "rise", "Rise", AttributeValueType.enum,
                 ["low", "mid", "high"])

    # Men's Trousers
    mtrousers_id = _get("men-trousers").id
    _upsert_attr(session, mtrousers_id, "fit", "Fit", AttributeValueType.enum,
                 ["slim", "straight", "relaxed", "tapered"])
    _upsert_attr(session, mtrousers_id, "length", "Length", AttributeValueType.enum,
                 ["full", "ankle", "cropped"])

    # Women's Jackets
    wjackets_id = _get("women-jackets").id
    _upsert_attr(session, wjackets_id, "jacket_type", "Type", AttributeValueType.enum,
                 ["blazer", "bomber", "denim", "leather", "trench", "puffer"])
    _upsert_attr(session, wjackets_id, "fit", "Fit", AttributeValueType.enum,
                 ["slim", "regular", "oversized"])

    # Men's Jackets
    mjackets_id = _get("men-jackets").id
    _upsert_attr(session, mjackets_id, "jacket_type", "Type", AttributeValueType.enum,
                 ["blazer", "bomber", "denim", "leather", "trench", "puffer"])
    _upsert_attr(session, mjackets_id, "fit", "Fit", AttributeValueType.enum,
                 ["slim", "regular", "relaxed"])

    # Kurtas & Kurtis
    kurta_id = _get("kurtas-kurtis").id
    _upsert_attr(session, kurta_id, "kurta_length", "Kurta Length", AttributeValueType.enum,
                 ["short (hip)", "mid (thigh)", "long (knee)", "extra-long (calf)"])
    _upsert_attr(session, kurta_id, "neckline", "Neckline", AttributeValueType.enum,
                 ["round", "v-neck", "mandarin", "sweetheart", "keyhole"])
    _upsert_attr(session, kurta_id, "sleeve_length", "Sleeve Length", AttributeValueType.enum,
                 ["sleeveless", "short", "3/4", "full"])
    _upsert_attr(session, kurta_id, "silhouette", "Silhouette", AttributeValueType.enum,
                 ["straight", "a-line", "flared", "high-low", "asymmetric"])
    _upsert_attr(session, kurta_id, "print_pattern", "Print / Pattern", AttributeValueType.enum,
                 ["solid", "block print", "floral", "geometric", "bandhani", "ikat", "embroidered"])

    # Sarees
    saree_id = _get("sarees").id
    _upsert_attr(session, saree_id, "saree_type", "Saree Type", AttributeValueType.enum,
                 ["silk", "cotton", "georgette", "chiffon", "linen", "banarasi", "kanjivaram",
                  "chanderi", "tussar", "organza"])
    _upsert_attr(session, saree_id, "blouse_included", "Blouse Included", AttributeValueType.enum,
                 ["yes", "no", "unstitched blouse piece"])
    _upsert_attr(session, saree_id, "work_type", "Work / Embellishment", AttributeValueType.enum,
                 ["plain", "printed", "embroidered", "zari", "sequin", "mirror work", "tie-dye"])

    # Lehengas
    lehenga_id = _get("lehengas").id
    _upsert_attr(session, lehenga_id, "lehenga_type", "Lehenga Type", AttributeValueType.enum,
                 ["bridal", "party wear", "casual", "festive"])
    _upsert_attr(session, lehenga_id, "silhouette", "Silhouette", AttributeValueType.enum,
                 ["a-line", "circular", "straight", "mermaid"])
    _upsert_attr(session, lehenga_id, "work_type", "Work / Embellishment", AttributeValueType.enum,
                 ["embroidered", "sequin", "zari", "mirror work", "printed", "plain"])
    _upsert_attr(session, lehenga_id, "set_pieces", "Set Pieces", AttributeValueType.enum,
                 ["2-piece (skirt + blouse)", "3-piece (skirt + blouse + dupatta)"])

    # Salwar Kameez
    salwar_id = _get("salwar-kameez").id
    _upsert_attr(session, salwar_id, "suit_type", "Suit Type", AttributeValueType.enum,
                 ["straight", "patiala", "churidar", "dhoti", "sharara", "palazzo"])
    _upsert_attr(session, salwar_id, "neckline", "Neckline", AttributeValueType.enum,
                 ["round", "v-neck", "mandarin", "sweetheart"])
    _upsert_attr(session, salwar_id, "sleeve_length", "Sleeve Length", AttributeValueType.enum,
                 ["sleeveless", "short", "3/4", "full"])
    _upsert_attr(session, salwar_id, "dupatta", "Dupatta", AttributeValueType.enum,
                 ["included", "not included"])

    # Anarkali Suits
    anarkali_id = _get("anarkali-suits").id
    _upsert_attr(session, anarkali_id, "suit_length", "Suit Length", AttributeValueType.enum,
                 ["knee length", "calf length", "floor length"])
    _upsert_attr(session, anarkali_id, "sleeve_length", "Sleeve Length", AttributeValueType.enum,
                 ["sleeveless", "short", "3/4", "full"])
    _upsert_attr(session, anarkali_id, "work_type", "Work / Embellishment", AttributeValueType.enum,
                 ["plain", "printed", "embroidered", "sequin", "zari"])

    # Coord Sets
    coord_id = _get("ethnic-coord-sets").id
    _upsert_attr(session, coord_id, "set_type", "Set Type", AttributeValueType.enum,
                 ["kurta + palazzo", "kurta + pant", "blouse + skirt", "top + sharara"])
    _upsert_attr(session, coord_id, "print_pattern", "Print / Pattern", AttributeValueType.enum,
                 ["solid", "printed", "embroidered", "block print"])

    # Dupattas & Stoles
    dupatta_id = _get("dupattas-stoles").id
    _upsert_attr(session, dupatta_id, "fabric", "Fabric", AttributeValueType.enum,
                 ["silk", "cotton", "chiffon", "georgette", "net", "linen", "wool"])
    _upsert_attr(session, dupatta_id, "work_type", "Work / Embellishment", AttributeValueType.enum,
                 ["plain", "printed", "embroidered", "zari border", "sequin", "mirror work"])

    # Kurtas & Sherwanis (Men)
    sherwani_id = _get("kurtas-sherwanis").id
    _upsert_attr(session, sherwani_id, "garment_type", "Garment Type", AttributeValueType.enum,
                 ["kurta", "sherwani", "indo-western", "achkan"])
    _upsert_attr(session, sherwani_id, "kurta_length", "Length", AttributeValueType.enum,
                 ["short (hip)", "mid (thigh)", "long (knee)", "extra-long (calf)"])
    _upsert_attr(session, sherwani_id, "neckline", "Neckline", AttributeValueType.enum,
                 ["mandarin", "band", "v-neck", "round"])
    _upsert_attr(session, sherwani_id, "sleeve_length", "Sleeve Length", AttributeValueType.enum,
                 ["short", "3/4", "full"])

    # Nehru Jackets
    nehru_id = _get("nehru-jackets").id
    _upsert_attr(session, nehru_id, "jacket_length", "Length", AttributeValueType.enum,
                 ["hip length", "knee length"])
    _upsert_attr(session, nehru_id, "fabric", "Fabric", AttributeValueType.enum,
                 ["silk", "cotton", "brocade", "velvet", "linen", "blended"])
    _upsert_attr(session, nehru_id, "work_type", "Work / Embellishment", AttributeValueType.enum,
                 ["plain", "embroidered", "printed", "zari"])

    # Dhotis & Lungis
    dhoti_id = _get("dhotis-lungis").id
    _upsert_attr(session, dhoti_id, "garment_type", "Garment Type", AttributeValueType.enum,
                 ["dhoti", "lungi", "dhoti pant"])
    _upsert_attr(session, dhoti_id, "fabric", "Fabric", AttributeValueType.enum,
                 ["cotton", "silk", "blended"])

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
