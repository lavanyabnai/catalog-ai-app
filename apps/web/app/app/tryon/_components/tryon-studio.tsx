"use client";

import { useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Sparkles, Upload, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { compressImage } from "@/lib/compress-image";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const SAMPLE_PERSONS: Sample[] = [
  {
    url: "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=768&q=85",
    thumb: "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=120&h=160&fit=crop&crop=top&q=75",
    label: "Model 1",
  },
  {
    url: "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=768&q=85",
    thumb: "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=120&h=160&fit=crop&crop=top&q=75",
    label: "Model 2",
  },
  {
    url: "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=768&q=85",
    thumb: "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=120&h=160&fit=crop&crop=top&q=75",
    label: "Model 3",
  },
  {
    url: "https://images.unsplash.com/photo-1488161628813-04466f872be2?w=768&q=85",
    thumb: "https://images.unsplash.com/photo-1488161628813-04466f872be2?w=120&h=160&fit=crop&crop=top&q=75",
    label: "Model 4",
  },
];

const SAMPLE_GARMENTS: Sample[] = [
  {
    url: "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=768&q=85",
    thumb: "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=120&h=160&fit=crop&q=75",
    label: "Dress",
  },
  {
    url: "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=768&q=85",
    thumb: "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=120&h=160&fit=crop&q=75",
    label: "Jacket",
  },
  {
    url: "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=768&q=85",
    thumb: "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=120&h=160&fit=crop&q=75",
    label: "Shirt",
  },
  {
    url: "https://images.unsplash.com/photo-1512436991641-6745cdb1723f?w=768&q=85",
    thumb: "https://images.unsplash.com/photo-1512436991641-6745cdb1723f?w=120&h=160&fit=crop&q=75",
    label: "Top",
  },
];

// ─── Types ───────────────────────────────────────────────────────────────────

interface Sample {
  url: string;
  thumb: string;
  label: string;
}

type ImagePayload =
  | { type: "url"; url: string }
  | { type: "b64"; base64: string; mediaType: string };

interface ImageState {
  preview: string;
  payload: ImagePayload;
}

// ─── DropZone ────────────────────────────────────────────────────────────────

function DropZone({
  state,
  onFile,
  onClear,
  inputRef,
  busy,
}: {
  state: ImageState | null;
  onFile: (f: File) => void;
  onClear: () => void;
  inputRef: React.RefObject<HTMLInputElement>;
  busy: boolean;
}) {
  const [dragging, setDragging] = useState(false);

  const pick = (f: File) => {
    if (f.type.startsWith("image/")) onFile(f);
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => !state && !busy && inputRef.current?.click()}
      onKeyDown={(e) => e.key === "Enter" && !state && !busy && inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        if (!busy && !state) setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        const f = e.dataTransfer.files[0];
        if (f) pick(f);
      }}
      className={cn(
        "relative flex items-center justify-center rounded-xl border-2 border-dashed",
        "h-[280px] overflow-hidden bg-muted/30 transition-all",
        !state && !busy && "cursor-pointer hover:border-primary/60 hover:bg-muted/50",
        dragging && "border-primary bg-primary/5 scale-[1.01]",
        state ? "border-border" : "border-border/60",
        busy && !state && "cursor-not-allowed opacity-60",
      )}
    >
      {state ? (
        <>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={state.preview}
            alt="Selected"
            className="h-full w-full object-contain"
          />
          {!busy && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onClear();
              }}
              className="absolute right-2 top-2 rounded-full bg-background/90 p-1.5 shadow-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </>
      ) : (
        <div className="flex flex-col items-center gap-3 px-8 text-center">
          <div className="rounded-full bg-muted p-3.5">
            <Upload className="h-5 w-5 text-muted-foreground" />
          </div>
          <div>
            <p className="text-sm font-medium">
              {dragging ? "Drop to select" : "Drop image here"}
            </p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              or click to browse · JPG, PNG, WEBP
            </p>
          </div>
        </div>
      )}

      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        disabled={busy}
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) pick(f);
          e.target.value = "";
        }}
      />
    </div>
  );
}

// ─── SampleGrid ──────────────────────────────────────────────────────────────

function SampleGrid({
  samples,
  selected,
  onSelect,
  busy,
}: {
  samples: Sample[];
  selected: string | null;
  onSelect: (url: string) => void;
  busy: boolean;
}) {
  return (
    <div className="mt-4">
      <p className="mb-2 text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
        Try an example
      </p>
      <div className="grid grid-cols-4 gap-2">
        {samples.map((s) => (
          <button
            key={s.url}
            type="button"
            disabled={busy}
            title={s.label}
            onClick={() => onSelect(s.url)}
            className={cn(
              "relative aspect-[3/4] overflow-hidden rounded-lg border-2 transition-all",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
              !busy && "hover:scale-[1.06]",
              selected === s.url
                ? "border-primary shadow-md ring-2 ring-primary/20"
                : "border-border/60 hover:border-primary/50",
              busy && "cursor-not-allowed opacity-50 pointer-events-none",
            )}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={s.thumb}
              alt={s.label}
              className="h-full w-full object-cover"
            />
            {selected === s.url && (
              <div className="absolute inset-0 flex items-center justify-center bg-primary/10">
                <span className="rounded-full bg-primary px-1.5 py-px text-[9px] font-bold text-primary-foreground">
                  ✓
                </span>
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Panel ───────────────────────────────────────────────────────────────────

function Panel({
  title,
  subtitle,
  state,
  samples,
  inputRef,
  busy,
  onFile,
  onClear,
  onSample,
}: {
  title: string;
  subtitle: string;
  state: ImageState | null;
  samples: Sample[];
  inputRef: React.RefObject<HTMLInputElement>;
  busy: boolean;
  onFile: (f: File) => void;
  onClear: () => void;
  onSample: (url: string) => void;
}) {
  const selectedUrl =
    state?.payload.type === "url" ? state.payload.url : null;

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <div className="mb-4">
        <h2 className="text-sm font-semibold">{title}</h2>
        <p className="mt-0.5 text-xs text-muted-foreground">{subtitle}</p>
      </div>

      <DropZone
        state={state}
        onFile={onFile}
        onClear={onClear}
        inputRef={inputRef}
        busy={busy}
      />

      <SampleGrid
        samples={samples}
        selected={selectedUrl}
        onSelect={onSample}
        busy={busy}
      />
    </div>
  );
}

// ─── TryOnStudio ─────────────────────────────────────────────────────────────

type Category = "tops" | "bottoms" | "one-pieces";

const CATEGORIES: { value: Category; label: string }[] = [
  { value: "tops", label: "Tops / Shirts" },
  { value: "bottoms", label: "Bottoms / Pants" },
  { value: "one-pieces", label: "Dresses / One-pieces" },
];

export function TryOnStudio({ token }: { token: string }) {
  const router = useRouter();
  const [person, setPerson] = useState<ImageState | null>(null);
  const [garment, setGarment] = useState<ImageState | null>(null);
  const [category, setCategory] = useState<Category>("tops");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const personRef = useRef<HTMLInputElement>(null!);
  const garmentRef = useRef<HTMLInputElement>(null!);

  const handleFile = useCallback(
    async (file: File, setter: (s: ImageState) => void) => {
      try {
        const { base64, mediaType } = await compressImage(file, 1200, 0.88);
        setter({
          preview: `data:${mediaType};base64,${base64}`,
          payload: { type: "b64", base64, mediaType },
        });
      } catch {
        // ignore; user can retry
      }
    },
    [],
  );

  const selectSample = useCallback(
    (url: string, setter: (s: ImageState) => void) => {
      setter({ preview: url, payload: { type: "url", url } });
    },
    [],
  );

  const runTryOn = async () => {
    if (!person || !garment) return;
    setError(null);
    setLoading(true);

    try {
      const body: Record<string, string> = {};

      if (person.payload.type === "url") {
        body.person_image_url = person.payload.url;
      } else {
        body.person_image_b64 = person.payload.base64;
        body.person_media_type = person.payload.mediaType;
      }

      if (garment.payload.type === "url") {
        body.garment_image_url = garment.payload.url;
      } else {
        body.garment_image_b64 = garment.payload.base64;
        body.garment_media_type = garment.payload.mediaType;
      }

      body.category = category;

      const res = await fetch(`${API_BASE}/api/v1/tryon`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(
          (err as { detail?: string }).detail ?? "Generation failed",
        );
      }

      const data = (await res.json()) as { result_url: string };
      const personPreview = person.preview;
      const garmentPreview = garment.preview;
      router.push(
        `/app/tryon/result?url=${encodeURIComponent(data.result_url)}&person=${encodeURIComponent(personPreview)}&garment=${encodeURIComponent(garmentPreview)}&category=${category}`,
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  const canRun = !!person && !!garment && !loading;

  const hintText = !person && !garment
    ? "Select a person photo and a garment to begin"
    : !person
    ? "Select a person photo to continue"
    : !garment
    ? "Select a garment image to continue"
    : null;

  return (
    <div className="space-y-6">
      {/* ── Input panels ─────────────────────────────────────────── */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Panel
          title="Person Photo"
          subtitle="Full-body photo on a plain background works best"
          state={person}
          samples={SAMPLE_PERSONS}
          inputRef={personRef}
          busy={loading}
          onFile={(f) => handleFile(f, setPerson)}
          onClear={() => setPerson(null)}
          onSample={(url) => selectSample(url, setPerson)}
        />

        <Panel
          title="Garment Image"
          subtitle="Flat lay, mannequin, or model product shot"
          state={garment}
          samples={SAMPLE_GARMENTS}
          inputRef={garmentRef}
          busy={loading}
          onFile={(f) => handleFile(f, setGarment)}
          onClear={() => setGarment(null)}
          onSample={(url) => selectSample(url, setGarment)}
        />
      </div>

      {/* ── Garment category ─────────────────────────────────────── */}
      <div className="flex items-center gap-4 rounded-xl border border-border bg-card px-5 py-3.5">
        <p className="text-xs font-semibold text-muted-foreground shrink-0">Garment type</p>
        <div className="flex gap-2 flex-wrap">
          {CATEGORIES.map((c) => (
            <button
              key={c.value}
              type="button"
              disabled={loading}
              onClick={() => setCategory(c.value)}
              className={cn(
                "rounded-full border px-4 py-1.5 text-xs font-medium transition-all",
                category === c.value
                  ? "border-foreground bg-foreground text-background"
                  : "border-border text-muted-foreground hover:border-foreground/40 hover:text-foreground",
                loading && "cursor-not-allowed opacity-50",
              )}
            >
              {c.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Error ────────────────────────────────────────────────── */}
      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* ── Generate CTA ─────────────────────────────────────────── */}
      <div className="flex flex-col items-center gap-2">
        <button
          onClick={runTryOn}
          disabled={!canRun}
          className={cn(
            "inline-flex items-center gap-2.5 rounded-full px-10 py-3 text-sm font-semibold transition-all",
            canRun
              ? "bg-foreground text-background shadow-md hover:opacity-85 active:scale-[0.98]"
              : "cursor-not-allowed bg-muted text-muted-foreground",
          )}
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Generating try-on…
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" />
              Try On
            </>
          )}
        </button>

        {loading ? (
          <p className="animate-pulse text-xs text-muted-foreground">
            This typically takes 30–60 seconds
          </p>
        ) : hintText ? (
          <p className="text-xs text-muted-foreground">{hintText}</p>
        ) : null}
      </div>

    </div>
  );
}
