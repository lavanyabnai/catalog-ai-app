import { notFound } from "next/navigation";
import { apiGet } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { StudioView } from "./_components/studio-view";

interface PersonaRead {
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

interface ProductRead {
  id: string;
  code: string;
  name: string;
  status: string;
  source_image_key: string | null;
  attributes: Record<string, unknown>;
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
    motion?: string;
    duration_seconds?: number;
  };
  params: Record<string, unknown>;
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

export interface BundleRead {
  id: string;
  version: number;
  status: "pending" | "approved";
  approved_at: string | null;
  assets: AssetRead[];
  jobs: JobRead[];
}

export default async function StudioPage({
  params,
}: {
  params: { id: string };
}) {
  const token = await getToken();

  let product: ProductRead | null = null;
  try {
    product = await apiGet<ProductRead>(`/api/v1/products/${params.id}`, token ?? undefined);
  } catch (err: unknown) {
    if (err instanceof Error && err.message.includes("404")) notFound();
    throw err;
  }
  if (!product) notFound();

  let bundle: BundleRead | null = null;
  try {
    bundle = await apiGet<BundleRead>(`/api/v1/products/${params.id}/bundle`, token ?? undefined);
  } catch {
    // No bundle yet
  }

  let personas: PersonaRead[] = [];
  try {
    personas = await apiGet<PersonaRead[]>("/api/v1/personas", token ?? undefined);
  } catch {
    // Non-fatal
  }

  return (
    <StudioView
      product={product}
      initialBundle={bundle}
      personas={personas}
      token={token ?? ""}
    />
  );
}
