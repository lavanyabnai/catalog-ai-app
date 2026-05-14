export interface ProductListItem {
  id: string;
  code: string;
  name: string;
  status: string;
  source_image_key: string | null;
  created_at: string;
}

export interface ProductRead extends ProductListItem {
  updated_at: string;
  attributes: Record<string, string | undefined>;
}

export interface AssetRead {
  id: string;
  kind: string;
  storage_key: string;
  width: number | null;
  height: number | null;
  mime_type: string;
  asset_metadata: Record<string, unknown>;
  is_hero: boolean;
}

export interface BundleRead {
  id: string;
  version: number;
  status: string;
  assets: AssetRead[];
}

// Unsplash fashion images (stable IDs — no auth needed)
const IMG = {
  kurta:    "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=600&q=80",
  saree:    "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=600&q=80",
  lehenga:  "https://images.unsplash.com/photo-1617627143750-d86bc21e42bb?w=600&q=80",
  dress:    "https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=600&q=80",
  jacket:   "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=600&q=80",
  trousers: "https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=600&q=80",
};

export const SAMPLE_PRODUCTS: ProductRead[] = [
  {
    id: "p1",
    code: "KRT-001",
    name: "Indigo Block-Print Kurta",
    status: "approved",
    source_image_key: IMG.kurta,
    created_at: "2026-05-10T08:00:00Z",
    updated_at: "2026-05-11T12:00:00Z",
    attributes: { material: "Cotton", size_range: "XS – 3XL" },
  },
  {
    id: "p2",
    code: "SAR-014",
    name: "Banarasi Silk Saree – Crimson",
    status: "ready_for_review",
    source_image_key: IMG.saree,
    created_at: "2026-05-11T09:30:00Z",
    updated_at: "2026-05-12T15:00:00Z",
    attributes: { material: "Silk", size_range: "Free size" },
  },
  {
    id: "p3",
    code: "LHG-007",
    name: "Mirror-Work Lehenga Set",
    status: "processing",
    source_image_key: IMG.lehenga,
    created_at: "2026-05-12T11:00:00Z",
    updated_at: "2026-05-12T11:00:00Z",
    attributes: { material: "Georgette", size_range: "S – XL" },
  },
  {
    id: "p4",
    code: "DRS-022",
    name: "Linen Midi Dress – Sand",
    status: "approved",
    source_image_key: IMG.dress,
    created_at: "2026-05-08T07:00:00Z",
    updated_at: "2026-05-09T10:00:00Z",
    attributes: { material: "Linen", size_range: "XS – XL" },
  },
  {
    id: "p5",
    code: "JKT-003",
    name: "Structured Blazer – Charcoal",
    status: "draft",
    source_image_key: IMG.jacket,
    created_at: "2026-05-13T14:00:00Z",
    updated_at: "2026-05-13T14:00:00Z",
    attributes: { material: "Wool blend", size_range: "S – XXL" },
  },
  {
    id: "p6",
    code: "TRS-008",
    name: "Wide-Leg Trousers – Ivory",
    status: "approved",
    source_image_key: IMG.trousers,
    created_at: "2026-05-07T06:00:00Z",
    updated_at: "2026-05-08T09:00:00Z",
    attributes: { material: "Viscose", size_range: "XS – XXL" },
  },
];

export const SAMPLE_BUNDLES: Record<string, BundleRead> = {
  p1: {
    id: "b1",
    version: 2,
    status: "approved",
    assets: [
      { id: "a1", kind: "image_on_model", storage_key: "https://images.unsplash.com/photo-1594938298603-c8148c4b4268?w=600&q=80", width: 800, height: 1200, mime_type: "image/jpeg", asset_metadata: { persona_name: "Priya · Ethnic" }, is_hero: true },
      { id: "a2", kind: "image_on_model", storage_key: "https://images.unsplash.com/photo-1568252542512-9fe8fe9c87bb?w=600&q=80", width: 800, height: 1200, mime_type: "image/jpeg", asset_metadata: { persona_name: "Anika · Studio" }, is_hero: false },
      { id: "a3", kind: "image_on_model", storage_key: "https://images.unsplash.com/photo-1537832816519-689ad163239b?w=600&q=80", width: 800, height: 1200, mime_type: "image/jpeg", asset_metadata: { persona_name: "Meera · Editorial" }, is_hero: false },
    ],
  },
  p4: {
    id: "b4",
    version: 1,
    status: "approved",
    assets: [
      { id: "a7", kind: "image_on_model", storage_key: "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600&q=80", width: 800, height: 1200, mime_type: "image/jpeg", asset_metadata: { persona_name: "Sofia · PDP" }, is_hero: true },
      { id: "a8", kind: "image_on_model", storage_key: "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=600&q=80", width: 800, height: 1200, mime_type: "image/jpeg", asset_metadata: { persona_name: "Zara · Editorial" }, is_hero: false },
    ],
  },
  p6: {
    id: "b6",
    version: 1,
    status: "approved",
    assets: [
      { id: "a10", kind: "image_on_model", storage_key: "https://images.unsplash.com/photo-1509631179647-0177331693ae?w=600&q=80", width: 800, height: 1200, mime_type: "image/jpeg", asset_metadata: { persona_name: "Anika · Studio" }, is_hero: true },
    ],
  },
};
