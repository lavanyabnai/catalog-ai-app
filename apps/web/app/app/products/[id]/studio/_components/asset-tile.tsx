"use client";

import type { AssetRead, JobRead } from "../page";

interface Props {
  job: JobRead;
  asset: AssetRead | null;
  jobStatus: "queued" | "running" | "succeeded" | "failed";
  isHero: boolean;
  bundleApproved: boolean;
  s3Base: string;
  onHeroClick: (assetId: string, isHero: boolean) => Promise<void>;
  onRegenerateClick: (assetId: string) => Promise<void>;
}

export function AssetTile({
  job,
  asset,
  jobStatus,
  isHero,
  bundleApproved,
  s3Base,
  onHeroClick,
  onRegenerateClick,
}: Props) {
  const persona = job.prompt.persona;
  const label = persona
    ? `${persona.display_name} · ${job.prompt.pose ?? ""}`
    : job.prompt.pose ?? "";

  if (jobStatus === "failed") {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/5 aspect-[4/5] flex flex-col items-center justify-center gap-2 p-2">
        <span className="text-xs text-destructive font-medium">Failed</span>
        <p className="text-[10px] text-muted-foreground text-center line-clamp-2">
          {job.error ?? "Generation error"}
        </p>
        {asset && !bundleApproved && (
          <button
            onClick={() => onRegenerateClick(asset.id)}
            className="text-[10px] text-primary underline hover:no-underline"
          >
            Retry
          </button>
        )}
      </div>
    );
  }

  if (!asset || jobStatus === "queued" || jobStatus === "running") {
    return (
      <div className="rounded-lg border bg-muted/30 aspect-[4/5] flex flex-col items-center justify-center gap-2 p-2 animate-pulse">
        <div className="w-8 h-8 rounded-full bg-muted" />
        <span className="text-[10px] text-muted-foreground capitalize">{jobStatus}</span>
      </div>
    );
  }

  // Succeeded with asset
  return (
    <div className="group relative rounded-lg border overflow-hidden bg-muted/30">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={`${s3Base}/${asset.storage_key}`}
        alt={label}
        className="w-full object-cover aspect-[4/5]"
      />

      {/* Overlay controls */}
      <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex flex-col justify-between p-1.5 opacity-0 group-hover:opacity-100">
        {/* Hero star — top right */}
        <div className="flex justify-end">
          <button
            title={isHero ? "Remove hero" : "Set as hero"}
            onClick={() => onHeroClick(asset.id, isHero)}
            className={`w-7 h-7 rounded-full flex items-center justify-center text-sm shadow transition-colors ${
              isHero
                ? "bg-yellow-400 text-yellow-900"
                : "bg-white/80 text-muted-foreground hover:bg-yellow-100 hover:text-yellow-600"
            }`}
          >
            {isHero ? "★" : "☆"}
          </button>
        </div>

        {/* Bottom: label + regenerate */}
        <div className="flex items-end justify-between gap-1">
          <p className="text-[10px] text-white drop-shadow line-clamp-1">{label}</p>
          {!bundleApproved && (
            <button
              title="Regenerate this shot"
              onClick={() => onRegenerateClick(asset.id)}
              className="w-6 h-6 rounded-full bg-white/80 text-muted-foreground hover:bg-white flex items-center justify-center text-[10px] shadow shrink-0"
            >
              ↺
            </button>
          )}
        </div>
      </div>

      {/* Hero badge — always visible when hero */}
      {isHero && (
        <div className="absolute top-1.5 left-1.5 bg-yellow-400 text-yellow-900 text-[9px] font-bold px-1.5 py-0.5 rounded-full">
          HERO
        </div>
      )}
    </div>
  );
}
