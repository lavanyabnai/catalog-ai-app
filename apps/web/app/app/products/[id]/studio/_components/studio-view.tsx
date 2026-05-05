"use client";

import { useEffect, useReducer, useRef, useState } from "react";
import { openSSEStream, apiGet, apiPost, apiDelete } from "@/lib/api";
import type { BundleRead, AssetRead, JobRead } from "../page";
import { AssetTile } from "./asset-tile";
import { VideoTile } from "./video-tile";
import { LeftRail } from "./left-rail";
import { RightRail } from "./right-rail";
import { BundleHistory } from "./bundle-history";

interface Persona {
  id: string;
  display_name: string;
  ethnicity: string;
  body_type: string;
  height_cm: number;
}

interface Product {
  id: string;
  name: string;
  code: string;
  status: string;
}

interface Props {
  product: Product;
  initialBundle: BundleRead | null;
  personas: Persona[];
  token: string;
}

interface State {
  bundle: BundleRead | null;
  jobStatuses: Record<string, "queued" | "running" | "succeeded" | "failed">;
  jobErrors: Record<string, string | null>;
  bundleStatus: "pending" | "approved";
  sseConnected: boolean;
  sseDone: boolean;
}

type Action =
  | { type: "SET_BUNDLE"; bundle: BundleRead }
  | { type: "JOB_STATUS"; jobId: string; status: "queued" | "running" | "succeeded" | "failed"; error: string | null }
  | { type: "BUNDLE_STATUS"; status: "pending" | "approved" }
  | { type: "SSE_CONNECTED" }
  | { type: "SSE_DONE" }
  | { type: "HERO_SET"; assetId: string }
  | { type: "HERO_UNSET"; assetId: string };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "SET_BUNDLE":
      return {
        ...state,
        bundle: action.bundle,
        bundleStatus: action.bundle.status,
        jobStatuses: Object.fromEntries(
          action.bundle.jobs.map((j) => [j.id, j.status])
        ),
        jobErrors: Object.fromEntries(
          action.bundle.jobs.map((j) => [j.id, j.error])
        ),
      };
    case "JOB_STATUS":
      return {
        ...state,
        jobStatuses: { ...state.jobStatuses, [action.jobId]: action.status },
        jobErrors: { ...state.jobErrors, [action.jobId]: action.error },
      };
    case "BUNDLE_STATUS":
      return {
        ...state,
        bundleStatus: action.status,
        bundle: state.bundle ? { ...state.bundle, status: action.status } : null,
      };
    case "SSE_CONNECTED":
      return { ...state, sseConnected: true };
    case "SSE_DONE":
      return { ...state, sseDone: true };
    case "HERO_SET":
      if (!state.bundle) return state;
      return {
        ...state,
        bundle: {
          ...state.bundle,
          assets: state.bundle.assets.map((a) => ({
            ...a,
            is_hero: a.id === action.assetId,
          })),
        },
      };
    case "HERO_UNSET":
      if (!state.bundle) return state;
      return {
        ...state,
        bundle: {
          ...state.bundle,
          assets: state.bundle.assets.map((a) =>
            a.id === action.assetId ? { ...a, is_hero: false } : a
          ),
        },
      };
    default:
      return state;
  }
}

const S3_BASE =
  typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_S3_PUBLIC_URL ?? "http://localhost:9000/catalog-ai")
    : "http://localhost:9000/catalog-ai";

export function StudioView({ product, initialBundle, personas, token }: Props) {
  const [tab, setTab] = useState<"gallery" | "history">("gallery");
  const [actionError, setActionError] = useState<string | null>(null);

  const [state, dispatch] = useReducer(reducer, {
    bundle: initialBundle,
    jobStatuses: Object.fromEntries(
      initialBundle?.jobs.map((j) => [j.id, j.status]) ?? []
    ),
    jobErrors: Object.fromEntries(
      initialBundle?.jobs.map((j) => [j.id, j.error]) ?? []
    ),
    bundleStatus: initialBundle?.status ?? "pending",
    sseConnected: false,
    sseDone: false,
  });

  const refetchBundle = async () => {
    try {
      const b = await apiGet<BundleRead>(
        `/api/v1/products/${product.id}/bundle`,
        token
      );
      dispatch({ type: "SET_BUNDLE", bundle: b });
    } catch {
      // ignore
    }
  };

  // SSE subscription — only while jobs are still running
  const cancelRef = useRef<(() => void) | null>(null);
  useEffect(() => {
    if (!state.bundle) return;
    if (state.sseDone) return;

    const cancel = openSSEStream(
      `/api/v1/products/${product.id}/events`,
      token,
      (event, data) => {
        if (event === "job_status") {
          const d = data as { job_id: string; status: "queued" | "running" | "succeeded" | "failed"; error: string | null };
          dispatch({ type: "JOB_STATUS", jobId: d.job_id, status: d.status, error: d.error });
          if (d.status === "succeeded") {
            refetchBundle();
          }
        } else if (event === "bundle_status") {
          const d = data as { status: "pending" | "approved" };
          dispatch({ type: "BUNDLE_STATUS", status: d.status });
        }
      },
      () => dispatch({ type: "SSE_DONE" }),
      (err) => console.error("SSE error:", err)
    );
    cancelRef.current = cancel;
    dispatch({ type: "SSE_CONNECTED" });

    return () => {
      cancel();
      cancelRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [product.id, token, state.sseDone]);

  const handleSetHero = async (assetId: string, isHero: boolean) => {
    setActionError(null);
    try {
      if (isHero) {
        await apiDelete(`/api/v1/assets/${assetId}/hero`, token);
        dispatch({ type: "HERO_UNSET", assetId });
      } else {
        await apiPost(`/api/v1/assets/${assetId}/hero`, {}, token);
        dispatch({ type: "HERO_SET", assetId });
      }
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Hero action failed");
    }
  };

  const handleRegenerate = async (assetId: string) => {
    setActionError(null);
    try {
      await apiPost(`/api/v1/assets/${assetId}/regenerate`, {}, token);
      dispatch({ type: "SSE_DONE" }); // reset so SSE reconnects
      await refetchBundle();
      setTimeout(() => dispatch({ type: "SSE_CONNECTED" }), 100);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Regeneration failed");
    }
  };

  const handleApprove = async () => {
    if (!state.bundle) return;
    setActionError(null);
    try {
      const updated = await apiPost<BundleRead>(
        `/api/v1/bundles/${state.bundle.id}/approve`,
        {},
        token
      );
      dispatch({ type: "SET_BUNDLE", bundle: updated });
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Approval failed");
    }
  };

  const { bundle } = state;
  const heroAsset = bundle?.assets.find((a) => a.is_hero) ?? null;
  const primaryAssets = bundle?.assets.filter((a) => a.kind === "image_on_model") ?? [];
  const videoAsset = bundle?.assets.find((a) => a.kind === "video_on_model") ?? null;
  const allJobs = bundle?.jobs ?? [];
  const imageJobs = allJobs.filter((j) => j.type === "image");
  const videoJob = allJobs.find((j) => j.type === "video") ?? null;

  // Build a map job_id → asset for primary images
  const assetByJob: Record<string, AssetRead> = {};
  for (const a of primaryAssets) {
    assetByJob[a.job_id] = a;
  }

  return (
    <div className="flex flex-col h-full">
      {/* Top bar */}
      <div className="flex items-center justify-between px-4 py-3 border-b shrink-0">
        <div>
          <h1 className="font-semibold text-sm">{product.name}</h1>
          <p className="text-xs text-muted-foreground font-mono">{product.code}</p>
        </div>
        <div className="flex items-center gap-2">
          {actionError && (
            <p className="text-xs text-destructive max-w-xs text-right">{actionError}</p>
          )}
          <TabButton active={tab === "gallery"} onClick={() => setTab("gallery")}>
            Gallery
          </TabButton>
          <TabButton active={tab === "history"} onClick={() => setTab("history")}>
            History
          </TabButton>
        </div>
      </div>

      {tab === "history" ? (
        <BundleHistory productId={product.id} token={token} s3Base={S3_BASE} />
      ) : (
        <div className="flex flex-1 min-h-0 overflow-hidden">
          {/* Left rail — personas used in this bundle */}
          <LeftRail jobs={imageJobs} personas={personas} />

          {/* Gallery */}
          <main className="flex-1 overflow-y-auto p-4 space-y-6">
            {imageJobs.length === 0 && !bundle ? (
              <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
                No images generated yet. Click Generate on the product page.
              </div>
            ) : (
              <>
                <div className="grid grid-cols-4 gap-3">
                  {imageJobs.map((job) => (
                    <AssetTile
                      key={job.id}
                      job={job}
                      asset={assetByJob[job.id] ?? null}
                      jobStatus={state.jobStatuses[job.id] ?? job.status}
                      isHero={assetByJob[job.id]?.is_hero ?? false}
                      bundleApproved={state.bundleStatus === "approved"}
                      s3Base={S3_BASE}
                      onHeroClick={handleSetHero}
                      onRegenerateClick={handleRegenerate}
                    />
                  ))}
                </div>

                {videoJob && (
                  <div>
                    <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                      On-Model Video
                    </h2>
                    <VideoTile
                      job={videoJob}
                      asset={videoAsset}
                      jobStatus={state.jobStatuses[videoJob.id] ?? videoJob.status}
                      s3Base={S3_BASE}
                    />
                  </div>
                )}
              </>
            )}
          </main>

          {/* Right rail — model spec + approve */}
          <RightRail
            bundle={bundle}
            heroAsset={heroAsset}
            bundleStatus={state.bundleStatus}
            onApprove={handleApprove}
            token={token}
            s3Base={S3_BASE}
          />
        </div>
      )}
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
        active
          ? "bg-primary text-primary-foreground"
          : "text-muted-foreground hover:text-foreground hover:bg-muted"
      }`}
    >
      {children}
    </button>
  );
}
