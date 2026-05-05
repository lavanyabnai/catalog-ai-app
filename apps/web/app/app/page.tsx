import Link from "next/link";
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

export default async function ProductsPage() {
  const token = await getToken();

  let data: ProductListResponse = { items: [], total: 0, cursor: null };
  try {
    data = await apiGet<ProductListResponse>("/api/v1/products", token ?? undefined);
  } catch {
    // API may not be running locally; show empty state
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold">Products</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {data.total} product{data.total !== 1 ? "s" : ""}
          </p>
        </div>
        <Link
          href="/app/new"
          className="inline-flex items-center justify-center rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          New product
        </Link>
      </div>

      {data.items.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-20 text-center">
          <p className="text-muted-foreground text-sm">No products yet.</p>
          <Link
            href="/app/new"
            className="mt-4 text-sm font-medium text-primary hover:underline"
          >
            Upload your first garment →
          </Link>
        </div>
      ) : (
        <div className="rounded-lg border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Code</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Name</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Status</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Created</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y">
              {data.items.map((p) => (
                <tr key={p.id} className="hover:bg-muted/30 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs">{p.code}</td>
                  <td className="px-4 py-3 font-medium">{p.name}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={p.status} />
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {new Date(p.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      href={`/app/products/${p.id}`}
                      className="text-primary hover:underline text-xs font-medium"
                    >
                      View →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    draft: "bg-slate-100 text-slate-700",
    processing: "bg-yellow-100 text-yellow-800",
    ready_for_review: "bg-blue-100 text-blue-800",
    approved: "bg-green-100 text-green-800",
    archived: "bg-red-100 text-red-700",
  };
  const label: Record<string, string> = {
    draft: "Draft",
    processing: "Processing",
    ready_for_review: "Ready for review",
    approved: "Approved",
    archived: "Archived",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${styles[status] ?? "bg-slate-100 text-slate-700"}`}
    >
      {label[status] ?? status}
    </span>
  );
}
