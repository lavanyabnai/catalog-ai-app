"use client";

import type { AssetRead, JobRead } from "../page";

interface Props {
  job: JobRead;
  asset: AssetRead | null;
  jobStatus: "queued" | "running" | "succeeded" | "failed";
  s3Base: string;
}

export function VideoTile({ job, asset, jobStatus, s3Base }: Props) {
  const posterKey = asset?.asset_metadata?.poster_key as string | undefined;
  const posterSrc = posterKey ? `${s3Base}/${posterKey}` : undefined;

  if (jobStatus === "failed") {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/5 p-4 flex items-center gap-3">
        <span className="text-destructive text-lg">&#9654;</span>
        <div>
          <p className="text-sm font-medium text-destructive">Video generation failed</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            {job.error ?? "An error occurred"}
          </p>
        </div>
      </div>
    );
  }

  if (jobStatus === "succeeded" && asset) {
    return (
      <div className="rounded-lg border overflow-hidden bg-black">
        <video
          controls
          preload="none"
          poster={posterSrc}
          className="w-full max-h-72 object-contain"
          src={asset.storage_key.startsWith("http") ? asset.storage_key : `${s3Base}/${asset.storage_key}`}
        />
        <div className="px-3 py-1.5 bg-muted/40 flex items-center justify-between">
          <span className="text-xs text-muted-foreground">
            On-model video
            {asset.duration_ms ? ` · ${(asset.duration_ms / 1000).toFixed(1)}s` : ""}
          </span>
          <a
            href={`${s3Base}/${asset.storage_key}`}
            download
            className="text-xs text-primary hover:underline"
          >
            Download
          </a>
        </div>
      </div>
    );
  }

  // queued or running
  const isWaitingForHero = jobStatus === "queued";
  return (
    <div
      className={`rounded-lg border bg-muted/20 p-4 flex items-center gap-3 ${
        jobStatus === "running" ? "animate-pulse" : ""
      }`}
    >
      <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center shrink-0">
        <span className="text-muted-foreground text-lg">&#9654;</span>
      </div>
      <div>
        <p className="text-sm font-medium">
          {jobStatus === "running" ? "Generating video…" : "Video"}
        </p>
        <p className="text-xs text-muted-foreground mt-0.5">
          {isWaitingForHero
            ? "Will start after a hero image is selected"
            : "Generating on-model video…"}
        </p>
      </div>
    </div>
  );
}
