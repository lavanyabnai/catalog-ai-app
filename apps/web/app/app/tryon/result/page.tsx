"use client";

import { Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { ArrowLeft, Download, RefreshCw, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

function Thumb({
  src,
  label,
  highlight,
}: {
  src: string;
  label: string;
  highlight?: boolean;
}) {
  return (
    <div className="text-center">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={src}
        alt={label}
        className={cn(
          "mx-auto h-24 w-16 rounded-lg border object-cover shadow-sm",
          highlight
            ? "border-primary/60 ring-2 ring-primary/25"
            : "border-border",
        )}
      />
      <p
        className={cn(
          "mt-1 text-[10px] font-medium",
          highlight ? "text-primary" : "text-muted-foreground",
        )}
      >
        {label}
      </p>
    </div>
  );
}

function TryOnResult() {
  const params = useSearchParams();
  const router = useRouter();

  const resultUrl  = params.get("url")      ?? "";
  const personSrc  = params.get("person")   ?? "";
  const garmentSrc = params.get("garment")  ?? "";
  const category   = params.get("category") ?? "tops";

  if (!resultUrl) {
    router.replace("/app/tryon");
    return null;
  }

  const categoryLabel =
    category === "bottoms" ? "Bottoms / Pants" :
    category === "one-pieces" ? "Dresses / One-pieces" :
    "Tops / Shirts";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/app/tryon")}
            className="rounded-full border border-border p-2 hover:bg-muted transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <h1 className="text-lg font-semibold">Try-On Result</h1>
            <p className="text-xs text-muted-foreground mt-0.5">
              AI-generated · {categoryLabel}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => router.push("/app/tryon")}
            className="inline-flex items-center gap-1.5 rounded-full border border-border px-4 py-2 text-xs font-medium hover:bg-muted transition-colors"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Try another
          </button>
          <a
            href={resultUrl}
            download="tryon-result.webp"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 rounded-full bg-foreground text-background px-4 py-2 text-xs font-semibold hover:opacity-85 transition-opacity"
          >
            <Download className="h-3.5 w-3.5" />
            Download
          </a>
        </div>
      </div>

      {/* Main content */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Full-size result — takes 2 cols */}
        <div className="lg:col-span-2 rounded-xl border border-border bg-card overflow-hidden">
          <div className="flex justify-center bg-muted/30 p-6 min-h-[500px] items-center">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={resultUrl}
              alt="Virtual try-on result"
              className="max-h-[640px] max-w-full rounded-xl object-contain shadow-lg"
            />
          </div>
        </div>

        {/* Right sidebar */}
        <div className="space-y-4">
          {/* Inputs used */}
          <div className="rounded-xl border border-border bg-card p-5">
            <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-4">
              Inputs used
            </h2>
            <div className="flex items-end gap-4">
              {personSrc && <Thumb src={personSrc} label="Person" />}
              <span className="pb-5 text-lg text-muted-foreground/40">+</span>
              {garmentSrc && <Thumb src={garmentSrc} label="Garment" />}
              <span className="pb-5 text-lg text-muted-foreground/40">→</span>
              <Thumb src={resultUrl} label="Result" highlight />
            </div>
          </div>

          {/* Actions */}
          <div className="rounded-xl border border-border bg-card p-5 space-y-3">
            <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
              Next steps
            </h2>

            <a
              href={resultUrl}
              download="tryon-result.webp"
              target="_blank"
              rel="noopener noreferrer"
              className="flex w-full items-center gap-2.5 rounded-lg border border-border px-4 py-3 text-sm hover:bg-muted transition-colors"
            >
              <Download className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="font-medium text-xs">Download result</p>
                <p className="text-[11px] text-muted-foreground">Save the generated image</p>
              </div>
            </a>

            <button
              onClick={() => router.push("/app/tryon")}
              className="flex w-full items-center gap-2.5 rounded-lg border border-border px-4 py-3 text-sm hover:bg-muted transition-colors"
            >
              <Sparkles className="h-4 w-4 text-muted-foreground" />
              <div className="text-left">
                <p className="font-medium text-xs">Try another combination</p>
                <p className="text-[11px] text-muted-foreground">
                  Different model or garment
                </p>
              </div>
            </button>

            <button
              onClick={() => router.push("/app/new")}
              className="flex w-full items-center gap-2.5 rounded-lg border border-border px-4 py-3 text-sm hover:bg-muted transition-colors"
            >
              <span className="h-4 w-4 flex items-center justify-center text-muted-foreground text-xs font-bold">+</span>
              <div className="text-left">
                <p className="font-medium text-xs">Add to catalog</p>
                <p className="text-[11px] text-muted-foreground">
                  Upload this garment as a new SKU
                </p>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function TryOnResultPage() {
  return (
    <Suspense>
      <TryOnResult />
    </Suspense>
  );
}
