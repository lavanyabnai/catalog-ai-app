import Link from "next/link";
import { Plus } from "lucide-react";
import { apiGet } from "@/lib/api";
import { getToken } from "@/lib/auth";

interface ProductListItem {
  id: string;
  code: string;
  name: string;
  status: string;
  source_image_key: string | null;
  created_at: string;
}

interface ProductListResponse {
  items: ProductListItem[];
  total: number;
  cursor: string | null;
}

const S3_BASE =
  process.env.NEXT_PUBLIC_S3_PUBLIC_URL ?? "http://localhost:9000/catalog-ai";

function imageUrl(key: string): string {
  return key.startsWith("http") ? key : `${S3_BASE}/${key}`;
}

const STATUS_LABEL: Record<string, string> = {
  draft: "Draft",
  processing: "Processing",
  ready_for_review: "Ready",
  approved: "Approved",
  archived: "Archived",
};

const STATUS_DOT: Record<string, string> = {
  draft: "bg-gray-300",
  processing: "bg-amber-400",
  ready_for_review: "bg-blue-400",
  approved: "bg-emerald-400",
  archived: "bg-red-300",
};

export default async function CatalogPage() {
  const token = await getToken();

  let data: ProductListResponse = { items: [], total: 0, cursor: null };
  try {
    data = await apiGet<ProductListResponse>("/api/v1/products", token ?? undefined);
  } catch {
    // API not reachable locally
  }

  return (
    <div>
      {/* Page header */}
      <div className="flex items-end justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {data.total > 0 ? `${data.total} Products` : "Products"}
          </h1>
          <p className="text-sm text-muted-foreground mt-1">All collections</p>
        </div>
        <Link
          href="/app/new"
          className="inline-flex items-center gap-1.5 bg-foreground text-background rounded-full px-5 py-2.5 text-sm font-medium hover:opacity-80 transition-opacity"
        >
          <Plus className="h-3.5 w-3.5" />
          New product
        </Link>
      </div>

      {/* Empty state */}
      {data.items.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed py-24 text-center">
          <div className="h-16 w-16 rounded-2xl bg-secondary flex items-center justify-center mb-4">
            <Plus className="h-7 w-7 text-muted-foreground" />
          </div>
          <p className="font-semibold text-base">No products yet</p>
          <p className="text-sm text-muted-foreground mt-1 mb-5">
            Upload your first garment to get started
          </p>
          <Link
            href="/app/new"
            className="inline-flex items-center gap-1.5 bg-foreground text-background rounded-full px-5 py-2.5 text-sm font-medium hover:opacity-80 transition-opacity"
          >
            <Plus className="h-3.5 w-3.5" />
            Upload garment
          </Link>
        </div>
      )}

      {/* Product grid */}
      {data.items.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {data.items.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>
      )}
    </div>
  );
}

function ProductCard({ product }: { product: ProductListItem }) {
  return (
    <Link href={`/app/products/${product.id}`} className="group block">
      <div className="bg-secondary/50 rounded-2xl overflow-hidden border border-border transition-shadow hover:shadow-md hover:bg-white">
        {/* Image */}
        <div className="aspect-[3/4] bg-muted overflow-hidden">
          {product.source_image_key ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={imageUrl(product.source_image_key)}
              alt={product.name}
              className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-500"
            />
          ) : (
            <div className="h-full w-full flex items-center justify-center">
              <span className="text-4xl font-bold text-muted-foreground/20 select-none">
                {product.name[0]?.toUpperCase()}
              </span>
            </div>
          )}
        </div>

        {/* Info */}
        <div className="p-3">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="font-semibold text-sm leading-tight truncate">{product.name}</p>
              <p className="text-xs text-muted-foreground mt-0.5 font-mono truncate">{product.code}</p>
            </div>
            <span className="flex items-center gap-1 shrink-0 mt-0.5">
              <span
                className={`h-1.5 w-1.5 rounded-full ${STATUS_DOT[product.status] ?? "bg-gray-300"}`}
              />
              <span className="text-[10px] text-muted-foreground">
                {STATUS_LABEL[product.status] ?? product.status}
              </span>
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}
