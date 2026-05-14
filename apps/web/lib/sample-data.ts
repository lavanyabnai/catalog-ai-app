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

export interface PersonaRead {
  id: string;
  display_name: string;
  ethnicity: string;
  body_type: string;
  age_range: string;
  height_cm: number;
  gender_presentation: string;
  hair: string;
  system_managed: boolean;
}

export interface AssetRead {
  id: string;
  job_id: string;
  kind: string;
  storage_key: string;
  width: number | null;
  height: number | null;
  duration_ms: number | null;
  mime_type: string;
  asset_metadata: Record<string, string | number | boolean | null>;
  version: number;
  is_hero: boolean;
  parent_asset_id: string | null;
}

export interface JobRead {
  id: string;
  type: "image" | "video";
  status: "queued" | "running" | "succeeded" | "failed";
  error: string | null;
  prompt: {
    persona?: PersonaRead;
    pose?: string;
    scene?: string;
  };
  params: Record<string, unknown>;
}

export interface BundleRead {
  id: string;
  version: number;
  status: "pending" | "approved";
  approved_at: string | null;
  assets: AssetRead[];
  jobs: JobRead[];
}

// Unsplash fashion images
const IMG = {
  kurta:    "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=600&q=80",
  saree:    "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=600&q=80",
  lehenga:  "https://images.unsplash.com/photo-1617627143750-d86bc21e42bb?w=600&q=80",
  dress:    "https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=600&q=80",
  jacket:   "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=600&q=80",
  trousers: "https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=600&q=80",
};

const MODEL_IMGS = [
  "https://images.unsplash.com/photo-1594938298603-c8148c4b4268?w=600&q=80",
  "https://images.unsplash.com/photo-1568252542512-9fe8fe9c87bb?w=600&q=80",
  "https://images.unsplash.com/photo-1537832816519-689ad163239b?w=600&q=80",
  "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600&q=80",
  "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=600&q=80",
  "https://images.unsplash.com/photo-1509631179647-0177331693ae?w=600&q=80",
];

export const SAMPLE_PERSONAS: PersonaRead[] = [
  { id: "per1", display_name: "Priya", ethnicity: "South Asian", body_type: "Athletic", age_range: "25–30", height_cm: 168, gender_presentation: "Feminine", hair: "Long black", system_managed: true },
  { id: "per2", display_name: "Anika", ethnicity: "South Asian", body_type: "Curvy", age_range: "28–35", height_cm: 162, gender_presentation: "Feminine", hair: "Medium wavy", system_managed: true },
  { id: "per3", display_name: "Meera", ethnicity: "South Asian", body_type: "Slim", age_range: "22–28", height_cm: 172, gender_presentation: "Feminine", hair: "Short straight", system_managed: true },
  { id: "per4", display_name: "Sofia", ethnicity: "European", body_type: "Athletic", age_range: "25–32", height_cm: 175, gender_presentation: "Feminine", hair: "Blonde long", system_managed: true },
];

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

function makeJob(id: string, persona: PersonaRead, pose: string, scene: string): JobRead {
  return {
    id,
    type: "image",
    status: "succeeded",
    error: null,
    prompt: { persona, pose, scene },
    params: {},
  };
}

function makeAsset(id: string, jobId: string, imgUrl: string, isHero = false): AssetRead {
  return {
    id,
    job_id: jobId,
    kind: "image_on_model",
    storage_key: imgUrl,
    width: 800,
    height: 1200,
    duration_ms: null,
    mime_type: "image/jpeg",
    asset_metadata: {},
    version: 1,
    is_hero: isHero,
    parent_asset_id: null,
  };
}

export const SAMPLE_BUNDLES: Record<string, BundleRead> = {
  p1: {
    id: "b1", version: 2, status: "approved", approved_at: "2026-05-11T14:00:00Z",
    jobs: [
      makeJob("j1a", SAMPLE_PERSONAS[0], "Standing", "Studio white"),
      makeJob("j1b", SAMPLE_PERSONAS[1], "Walking", "Outdoor natural"),
      makeJob("j1c", SAMPLE_PERSONAS[2], "Sitting", "Editorial grey"),
    ],
    assets: [
      makeAsset("a1a", "j1a", MODEL_IMGS[0], true),
      makeAsset("a1b", "j1b", MODEL_IMGS[1]),
      makeAsset("a1c", "j1c", MODEL_IMGS[2]),
    ],
  },
  p2: {
    id: "b2", version: 1, status: "pending", approved_at: null,
    jobs: [
      makeJob("j2a", SAMPLE_PERSONAS[0], "Standing", "Studio white"),
      makeJob("j2b", SAMPLE_PERSONAS[1], "Walking", "Outdoor natural"),
      makeJob("j2c", SAMPLE_PERSONAS[2], "Sitting", "Editorial grey"),
      makeJob("j2d", SAMPLE_PERSONAS[3], "Standing", "Studio gradient"),
    ],
    assets: [
      makeAsset("a2a", "j2a", MODEL_IMGS[0], true),
      makeAsset("a2b", "j2b", MODEL_IMGS[1]),
      makeAsset("a2c", "j2c", MODEL_IMGS[2]),
      makeAsset("a2d", "j2d", MODEL_IMGS[3]),
    ],
  },
  p4: {
    id: "b4", version: 1, status: "approved", approved_at: "2026-05-09T12:00:00Z",
    jobs: [
      makeJob("j4a", SAMPLE_PERSONAS[3], "Standing", "Studio white"),
      makeJob("j4b", SAMPLE_PERSONAS[0], "Walking", "Outdoor natural"),
    ],
    assets: [
      makeAsset("a4a", "j4a", MODEL_IMGS[3], true),
      makeAsset("a4b", "j4b", MODEL_IMGS[4]),
    ],
  },
  p6: {
    id: "b6", version: 1, status: "approved", approved_at: "2026-05-08T11:00:00Z",
    jobs: [
      makeJob("j6a", SAMPLE_PERSONAS[1], "Standing", "Studio white"),
    ],
    assets: [
      makeAsset("a6a", "j6a", MODEL_IMGS[5], true),
    ],
  },
};
