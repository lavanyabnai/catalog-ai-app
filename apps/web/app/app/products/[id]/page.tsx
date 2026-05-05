import Link from "next/link";
import { notFound } from "next/navigation";
import { apiGet } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { GenerateButton } from "./_components/generate-button";

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

const STATUS_LABEL: Record<string, string> = {
  draft: "Draft",
  processing: "Processing…",
  ready_for_review: "Ready for review",
  approved: "Approved",
  archived: "Archived",
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
  } catch (err: unknown) {
    if (err instanceof Error && err.message.includes("404")) notFound();
    throw err;
  }
  if (!product) notFound();

  let bundle: BundleRead | null = null;
  try {
    bundle = await apiGet<BundleRead>(`/api/v1/products/${params.id}/bundle`, token ?? undefined);
  } catch {
    // No bundle yet — fine
  }

  const S3_BASE =
    process.env.NEXT_PUBLIC_S3_PUBLIC_URL ?? "http://localhost:9000/catalog-ai";

  const canGenerate = !!product.source_image_key && product.status !== "processing";

  return (
    <div className="max-w-5xl">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold">{product.name}</h1>
          <p className="text-sm text-muted-foreground mt-0.5 font-mono">{product.code}</p>
        </div>
        <div className="flex items-center gap-2">
          {bundle && (
            <Link
              href={`/app/products/${product.id}/studio`}
              className="inline-flex items-center justify-center rounded-md border border-input px-4 py-2 text-sm font-medium hover:bg-muted transition-colors"
            >
              Open Studio →
            </Link>
          )}
          <GenerateButton
            productId={product.id}
            canGenerate={canGenerate}
            token={token ?? ""}
          />
        </div>
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-3 gap-6">
        {/* Source image */}
        <div className="col-span-1 space-y-3">
          <p className="text-sm font-medium">Source photo</p>
          {product.source_image_key ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={`${S3_BASE}/${product.source_image_key}`}
              alt={product.name}
              className="rounded-lg border w-full object-contain max-h-80 bg-muted"
            />
          ) : (
            <div className="rounded-lg border border-dashed flex items-center justify-center h-48 text-muted-foreground text-sm">
              No image uploaded
            </div>
          )}

          <div className="space-y-2 pt-1">
            <InfoRow label="Status" value={STATUS_LABEL[product.status] ?? product.status} />
            <InfoRow label="Code" value={product.code} mono />
            <InfoRow
              label="Created"
              value={new Date(product.created_at).toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            />
          </div>
        </div>

        {/* Generated assets */}
        <div className="col-span-2">
          <p className="text-sm font-medium mb-3">
            Generated images
            {bundle && (
              <span className="ml-2 text-xs text-muted-foreground font-normal">
                Bundle v{bundle.version} · {bundle.assets.length} asset
                {bundle.assets.length !== 1 ? "s" : ""}
              </span>
            )}
          </p>

          {bundle && bundle.assets.length > 0 ? (
            <div className="grid grid-cols-2 gap-3">
              {bundle.assets.map((asset) => (
                <div key={asset.id} className="rounded-lg border overflow-hidden bg-muted/30">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={`${S3_BASE}/${asset.storage_key}`}
                    alt="Generated asset"
                    className="w-full object-cover aspect-[4/5]"
                  />
                  {asset.asset_metadata.persona_name != null && (
                    <p className="text-xs text-muted-foreground px-2 py-1 truncate">
                      {`${asset.asset_metadata.persona_name} · ${asset.asset_metadata.pose ?? ""}`}
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-lg border border-dashed flex items-center justify-center h-48 text-center px-4">
              <div>
                <p className="text-sm text-muted-foreground">No generated images yet.</p>
                {product.source_image_key && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Click &ldquo;Generate&rdquo; to create on-model images.
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

function InfoRow({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div>
      <dt className="text-xs font-medium text-muted-foreground uppercase tracking-wide">{label}</dt>
      <dd className={`mt-0.5 text-sm ${mono ? "font-mono" : ""}`}>{value}</dd>
    </div>
  );
}
