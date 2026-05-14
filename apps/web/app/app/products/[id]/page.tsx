import Link from "next/link";
import { ChevronLeft, Layers, Wand2 } from "lucide-react";
import { notFound } from "next/navigation";
import { apiGet } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { GenerateButton } from "./_components/generate-button";
import { GenerationProgress } from "./_components/generation-progress";
import { ImageUploader } from "./_components/image-uploader";
import { SAMPLE_PRODUCTS, SAMPLE_BUNDLES } from "@/lib/sample-data";

interface ProductRead {
  id: string;
  code: string;
  name: string;
  status: string;
  source_image_key: string | null;
  created_at: string;
  updated_at: string;
  attributes: Record<string, unknown>;
}

interface AssetRead {
  id: string;
  kind: string;
  storage_key: string;
  width: number | null;
  height: number | null;
  mime_type: string;
  asset_metadata: Record<string, unknown>;
  is_hero: boolean;
}

interface BundleRead {
  id: string;
  version: number;
  status: string;
  assets: AssetRead[];
}

const S3_BASE =
  process.env.NEXT_PUBLIC_S3_PUBLIC_URL ?? "http://localhost:9000/catalog-ai";

function imageUrl(key: string): string {
  return key.startsWith("http") ? key : `${S3_BASE}/${key}`;
}

const STATUS_LABEL: Record<string, string> = {
  draft: "Draft",
  processing: "Processing…",
  ready_for_review: "Ready for review",
  approved: "Approved",
  archived: "Archived",
};

const STATUS_COLOR: Record<string, string> = {
  draft: "bg-stone-100 text-stone-600",
  processing: "bg-amber-100 text-amber-700",
  ready_for_review: "bg-blue-100 text-blue-700",
  approved: "bg-emerald-100 text-emerald-700",
  archived: "bg-red-100 text-red-600",
};

export default async function ProductDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const token = await getToken();

  let product: ProductRead | null = null;
  try {
    product = await apiGet<ProductRead>(`/api/v1/products/${params.id}`, token ?? undefined);
  } catch {
    product = (SAMPLE_PRODUCTS.find((p) => p.id === params.id) as ProductRead | undefined) ?? null;
  }
  if (!product) notFound();

  let bundle: BundleRead | null = null;
  try {
    bundle = await apiGet<BundleRead>(`/api/v1/products/${params.id}/bundle`, token ?? undefined);
  } catch {
    bundle = SAMPLE_BUNDLES[params.id] ?? null;
  }

  const canGenerate = !!product.source_image_key && product.status !== "processing";

  // Collect all source image keys (front + optional back/detail)
  const extraKeys = (product.attributes.extra_image_keys as string[] | undefined) ?? [];
  const allSourceKeys = [
    ...(product.source_image_key ? [product.source_image_key] : []),
    ...extraKeys,
  ];

  const primaryAssets = bundle?.assets.filter((a) => a.kind === "image_on_model") ?? [];
  const videoAsset = bundle?.assets.find((a) => a.kind === "video_on_model") ?? null;

  const attr = product.attributes as Record<string, string | undefined>;

  return (
    <div>
      {/* Back nav */}
      <Link
        href="/app"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors mb-6"
      >
        <ChevronLeft className="h-4 w-4" />
        Catalog
      </Link>

      <div className="grid grid-cols-5 gap-8">
        {/* ── Left: Source photos ─────────────────────────────────── */}
        <div className="col-span-2 space-y-3">
          {/* Hero image */}
          <div className="bg-white rounded-2xl overflow-hidden border border-border aspect-[3/4]">
            {allSourceKeys[0] ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={imageUrl(allSourceKeys[0])}
                alt={product.name}
                className="h-full w-full object-contain"
              />
            ) : (
              <ImageUploader productId={product.id} token={token ?? ""} />
            )}
          </div>

          {/* Thumbnail strip — back / detail views */}
          {allSourceKeys.length > 1 && (
            <div className="flex gap-2">
              {allSourceKeys.map((key, i) => (
                <div
                  key={key}
                  className={`flex-1 rounded-xl overflow-hidden border aspect-square bg-white ${
                    i === 0 ? "ring-2 ring-foreground" : "border-border"
                  }`}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={imageUrl(key)}
                    alt={`View ${i + 1}`}
                    className="h-full w-full object-cover"
                  />
                </div>
              ))}
              {/* Placeholder slots to always show 3 */}
              {Array.from({ length: Math.max(0, 3 - allSourceKeys.length) }).map((_, i) => (
                <div
                  key={`empty-${i}`}
                  className="flex-1 rounded-xl border border-dashed border-border aspect-square bg-muted/30"
                />
              ))}
            </div>
          )}
        </div>

        {/* ── Right: Info + actions ───────────────────────────────── */}
        <div className="col-span-3 space-y-6">
          {/* Product identity */}
          <div>
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="text-2xl font-bold leading-snug">{product.name}</h1>
                <p className="text-sm text-muted-foreground font-mono mt-1">{product.code}</p>
              </div>
              <span
                className={`shrink-0 mt-1 rounded-full px-2.5 py-1 text-xs font-medium ${
                  STATUS_COLOR[product.status] ?? "bg-stone-100 text-stone-600"
                }`}
              >
                {STATUS_LABEL[product.status] ?? product.status}
              </span>
            </div>
          </div>

          {/* Attributes */}
          <div className="bg-white rounded-2xl border border-border p-4 grid grid-cols-2 gap-4">
            {attr.material && <AttrRow label="Material" value={attr.material} />}
            {attr.size_range && <AttrRow label="Sizes" value={attr.size_range} />}
            <AttrRow
              label="Added"
              value={new Date(product.created_at).toLocaleDateString("en-US", {
                year: "numeric",
                month: "short",
                day: "numeric",
              })}
            />
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-3">
            <GenerateButton
              productId={product.id}
              canGenerate={canGenerate}
              token={token ?? ""}
            />
            {bundle && (
              <Link
                href={`/app/products/${product.id}/studio`}
                className="inline-flex items-center gap-1.5 rounded-full border border-border bg-white px-4 py-2 text-sm font-medium hover:bg-muted transition-colors"
              >
                <Layers className="h-3.5 w-3.5" />
                Open Studio
              </Link>
            )}
          </div>

          {/* Live generation progress */}
          {product.status === "processing" && (
            <GenerationProgress productId={product.id} token={token ?? ""} />
          )}

          {/* Skeleton grid while processing */}
          {product.status === "processing" && primaryAssets.length === 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Wand2 className="h-4 w-4 text-muted-foreground" />
                <p className="text-sm font-semibold">On-model images</p>
              </div>
              <div className="grid grid-cols-3 gap-3">
                {Array.from({ length: 9 }).map((_, i) => (
                  <div
                    key={i}
                    className="rounded-xl bg-muted/60 animate-pulse aspect-[3/4]"
                  />
                ))}
              </div>
            </div>
          )}

          {/* Generated images */}
          {primaryAssets.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Wand2 className="h-4 w-4 text-muted-foreground" />
                <p className="text-sm font-semibold">
                  On-model images
                  <span className="ml-2 text-xs font-normal text-muted-foreground">
                    Bundle v{bundle?.version} · {primaryAssets.length} image{primaryAssets.length !== 1 ? "s" : ""}
                  </span>
                </p>
              </div>
              <div className="grid grid-cols-3 gap-3">
                {primaryAssets.map((asset) => (
                  <div
                    key={asset.id}
                    className={`relative rounded-xl overflow-hidden bg-white border ${
                      asset.is_hero ? "ring-2 ring-foreground" : "border-border"
                    }`}
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={imageUrl(asset.storage_key)}
                      alt="Generated"
                      className="w-full object-cover aspect-[3/4]"
                    />
                    {asset.is_hero && (
                      <span className="absolute top-2 left-2 rounded-full bg-foreground text-background text-[10px] font-medium px-2 py-0.5">
                        Hero
                      </span>
                    )}
                    {asset.asset_metadata.persona_name != null && (
                      <p className="text-[10px] text-muted-foreground px-2 py-1 truncate">
                        {String(asset.asset_metadata.persona_name)}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Video */}
          {videoAsset && (
            <div>
              <p className="text-sm font-semibold mb-3 flex items-center gap-2">
                <Wand2 className="h-4 w-4 text-muted-foreground" />
                On-model video
              </p>
              <div className="rounded-xl overflow-hidden border border-border bg-white max-w-xs">
                <video
                  src={imageUrl(videoAsset.storage_key)}
                  controls
                  className="w-full aspect-[9/16] object-cover"
                />
              </div>
            </div>
          )}

          {/* Empty state */}
          {!bundle && product.status !== "processing" && (
            <div className="rounded-2xl border border-dashed border-border bg-white/50 flex items-center justify-center h-40 text-center px-6">
              <div>
                <p className="text-sm font-medium">No images generated yet</p>
                {canGenerate && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Click &ldquo;Generate&rdquo; to create on-model photos &amp; video
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function AttrRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-[10px] font-medium text-muted-foreground uppercase tracking-widest">
        {label}
      </dt>
      <dd className="mt-0.5 text-sm font-medium">{value}</dd>
    </div>
  );
}
