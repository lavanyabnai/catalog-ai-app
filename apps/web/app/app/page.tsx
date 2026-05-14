import Link from "next/link";
import { LayoutGrid } from "lucide-react";
import { apiGet } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { SAMPLE_PRODUCTS } from "@/lib/sample-data";

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

// Relative time label from ISO string
function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h`;
  return `${Math.floor(hrs / 24)}d`;
}

// Derive a human activity line from a product's status + timestamps
function activityLine(p: ProductListItem): string {
  switch (p.status) {
    case "processing":
      return `Generation agent is processing SKU ${p.code}`;
    case "ready_for_review":
      return `Generation agent finished bundle for SKU ${p.code}`;
    case "approved":
      return `Bundle approved for SKU ${p.code}`;
    default:
      return p.source_image_key
        ? `SKU ${p.code} uploaded — ready to generate`
        : `SKU ${p.code} created as draft`;
  }
}

export default async function WorkspacePage() {
  const token = await getToken();

  let data: ProductListResponse = { items: [], total: 0, cursor: null };
  try {
    data = await apiGet<ProductListResponse>("/api/v1/products", token ?? undefined);
  } catch {
    data = { items: SAMPLE_PRODUCTS, total: SAMPLE_PRODUCTS.length, cursor: null };
  }

  const live       = data.items.filter((p) => p.status === "approved").length;
  const generating = data.items.filter((p) => p.status === "processing").length;
  const reviewing  = data.items.filter((p) => p.status === "ready_for_review").length;

  // Activity feed: all products sorted newest first, last 6
  const activity = [...data.items]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 6);

  // Needs attention: ready-for-review products
  const attention = data.items.filter((p) => p.status === "ready_for_review").slice(0, 4);

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Catalog workspace</h1>
          <p className="text-sm text-muted-foreground mt-1">
            catalog-ai · all collections
          </p>
        </div>
        <Link
          href="/app/catalog"
          className="inline-flex items-center gap-1.5 bg-foreground text-background rounded-full px-5 py-2.5 text-sm font-medium hover:opacity-80 transition-opacity"
        >
          <LayoutGrid className="h-3.5 w-3.5" />
          View Catalog
        </Link>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard label="SKUs live"        value={live}       />
        <StatCard label="In generation"    value={generating} />
        <StatCard label="Awaiting review"  value={reviewing}  />
        <StatCard label="Total SKUs"       value={data.total} />
      </div>

      {/* Activity + Attention */}
      <div className="grid grid-cols-5 gap-6">
        {/* Agent activity */}
        <div className="col-span-3 rounded-xl border border-border bg-card p-6">
          <h2 className="font-semibold text-sm mb-4">Agent activity</h2>

          {activity.length === 0 ? (
            <p className="text-sm text-muted-foreground py-8 text-center">
              No activity yet —{" "}
              <Link href="/app/new" className="underline underline-offset-2">
                upload your first SKU
              </Link>
            </p>
          ) : (
            <ul className="divide-y divide-border">
              {activity.map((p) => (
                <li key={p.id} className="flex items-center justify-between py-3.5 gap-4">
                  <Link
                    href={`/app/products/${p.id}`}
                    className="text-sm text-foreground hover:underline underline-offset-2 line-clamp-1"
                  >
                    {activityLine(p)}
                  </Link>
                  <span className="text-xs text-muted-foreground shrink-0 tabular-nums">
                    {relativeTime(p.created_at)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Needs your attention */}
        <div className="col-span-2 space-y-3">
          <h2 className="font-semibold text-sm">Needs your attention</h2>

          {attention.length === 0 ? (
            <div className="rounded-xl border border-border bg-card p-5 text-sm text-muted-foreground">
              Nothing needs attention right now.
            </div>
          ) : (
            attention.map((p) => (
              <Link
                key={p.id}
                href={`/app/products/${p.id}/studio`}
                className="block rounded-xl bg-amber-50 border border-amber-100 px-4 py-3.5 hover:bg-amber-100 transition-colors"
              >
                <p className="text-sm font-semibold text-amber-800">
                  {p.name}
                </p>
                <p className="text-xs text-amber-600 mt-0.5">
                  SKU {p.code} · ready for review
                </p>
              </Link>
            ))
          )}

          {/* Divider + link to catalog */}
          <div className="pt-2">
            <Link
              href="/app/catalog"
              className="text-xs text-muted-foreground hover:text-foreground transition-colors underline underline-offset-2"
            >
              View all {data.total} products →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-xl border border-border bg-secondary/60 px-5 py-4">
      <p className="text-xs text-muted-foreground mb-2">{label}</p>
      <p className="text-3xl font-bold tracking-tight">{value}</p>
    </div>
  );
}
