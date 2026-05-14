"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

interface BundleListItem {
  id: string;
  version: number;
  status: "pending" | "approved";
  created_at: string;
  total_assets: number;
  hero_storage_key: string | null;
}

interface Props {
  productId: string;
  token: string;
  s3Base: string;
}

export function BundleHistory({ productId, token, s3Base }: Props) {
  const [bundles, setBundles] = useState<BundleListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGet<BundleListItem[]>(`/api/v1/products/${productId}/bundles`, token)
      .then(setBundles)
      .catch(() => setBundles([]))
      .finally(() => setLoading(false));
  }, [productId, token]);

  if (loading) {
    return (
      <div className="flex-1 p-6 flex items-center justify-center text-sm text-muted-foreground">
        Loading history…
      </div>
    );
  }

  if (bundles.length === 0) {
    return (
      <div className="flex-1 p-6 flex items-center justify-center text-sm text-muted-foreground">
        No bundles yet.
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4">
      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">
        Bundle history
      </p>
      <div className="space-y-2">
        {bundles.map((b) => (
          <div
            key={b.id}
            className="rounded-lg border p-3 flex items-center gap-3 hover:bg-muted/30 transition-colors"
          >
            {/* Thumbnail */}
            <div className="w-12 h-14 rounded shrink-0 overflow-hidden bg-muted/50">
              {b.hero_storage_key ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={b.hero_storage_key.startsWith("http") ? b.hero_storage_key : `${s3Base}/${b.hero_storage_key}`}
                  alt={`v${b.version} hero`}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-[10px] text-muted-foreground">
                  —
                </div>
              )}
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">v{b.version}</span>
                <StatusBadge status={b.status} />
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                {b.total_assets} asset{b.total_assets !== 1 ? "s" : ""}
              </p>
              <p className="text-[10px] text-muted-foreground">
                {new Date(b.created_at).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: "pending" | "approved" }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-1.5 py-0.5 text-[9px] font-semibold ${
        status === "approved"
          ? "bg-green-100 text-green-800"
          : "bg-muted text-muted-foreground"
      }`}
    >
      {status === "approved" ? "Approved" : "Pending"}
    </span>
  );
}
