"use client";

import { useState } from "react";
import type { AssetRead, BundleRead } from "../page";

interface Props {
  bundle: BundleRead | null;
  heroAsset: AssetRead | null;
  bundleStatus: "pending" | "approved";
  onApprove: () => Promise<void>;
  token: string;
  s3Base: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function RightRail({ bundle, heroAsset, bundleStatus, onApprove, token, s3Base }: Props) {
  const [approving, setApproving] = useState(false);

  const handleApprove = async () => {
    setApproving(true);
    try {
      await onApprove();
    } finally {
      setApproving(false);
    }
  };

  const modelSpec = heroAsset?.asset_metadata ?? {};
  const heightImperial = modelSpec.model_height_imperial as string | undefined;
  const heightCm = modelSpec.model_height_cm as number | undefined;
  const garmentSize = modelSpec.garment_size_worn as string | undefined;

  return (
    <aside className="w-[220px] shrink-0 border-l overflow-y-auto p-3 space-y-4">
      {/* Status badge */}
      <div>
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">
          Bundle
        </p>
        <span
          className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ${
            bundleStatus === "approved"
              ? "bg-green-100 text-green-800"
              : "bg-muted text-muted-foreground"
          }`}
        >
          {bundleStatus === "approved" ? "Approved" : "Pending review"}
        </span>
        {bundle && (
          <p className="text-[10px] text-muted-foreground mt-1">v{bundle.version}</p>
        )}
      </div>

      {/* Model spec card */}
      {heroAsset ? (
        <div className="space-y-1.5">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
            Hero model spec
          </p>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={`${s3Base}/${heroAsset.storage_key}`}
            alt="Hero"
            className="w-full object-cover aspect-[4/5] rounded-md border"
          />
          {(heightImperial || heightCm) && (
            <SpecRow label="Height">
              {heightImperial ?? `${heightCm} cm`}
            </SpecRow>
          )}
          {garmentSize && <SpecRow label="Garment size">{garmentSize}</SpecRow>}
          {heroAsset.width && heroAsset.height && (
            <SpecRow label="Resolution">
              {heroAsset.width} × {heroAsset.height}
            </SpecRow>
          )}
        </div>
      ) : (
        <div className="rounded-md border border-dashed p-3 text-center">
          <p className="text-[10px] text-muted-foreground">
            Hover an image and click ☆ to select a hero.
          </p>
        </div>
      )}

      {/* Compliance placeholder */}
      <div className="rounded-md bg-muted/50 p-2">
        <p className="text-[10px] text-muted-foreground font-medium">Compliance checks</p>
        <p className="text-[10px] text-muted-foreground mt-0.5">Coming soon — Session 8</p>
      </div>

      {/* Actions */}
      <div className="space-y-2 pt-1">
        {bundleStatus !== "approved" && (
          <button
            onClick={handleApprove}
            disabled={!heroAsset || approving}
            className="w-full rounded-md bg-primary text-primary-foreground text-xs font-medium py-2 hover:bg-primary/90 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {approving ? "Approving…" : "Approve bundle"}
          </button>
        )}

        {bundleStatus === "approved" && bundle && (
          <a
            href={`${API_BASE}/api/v1/bundles/${bundle.id}/download`}
            onClick={(e) => {
              // Attach token via fetch instead of direct anchor
              e.preventDefault();
              downloadBundle(bundle.id, token);
            }}
            className="w-full rounded-md border border-primary text-primary text-xs font-medium py-2 flex items-center justify-center hover:bg-primary/5 transition-colors"
          >
            Download zip
          </a>
        )}

        {bundleStatus !== "approved" && !heroAsset && (
          <p className="text-[10px] text-muted-foreground text-center">
            Select a hero image to enable approval.
          </p>
        )}
      </div>
    </aside>
  );
}

async function downloadBundle(bundleId: string, token: string) {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const res = await fetch(`${API_BASE_URL}/api/v1/bundles/${bundleId}/download`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) return;
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `bundle_${bundleId}.zip`;
  a.click();
  URL.revokeObjectURL(url);
}

function SpecRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex justify-between items-baseline">
      <span className="text-[10px] text-muted-foreground">{label}</span>
      <span className="text-[10px] font-medium">{children}</span>
    </div>
  );
}
