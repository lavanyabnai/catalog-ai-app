"use client";

import { useRouter } from "next/navigation";
import { useCallback, useRef, useState } from "react";
import { Upload } from "lucide-react";
import { cn } from "@/lib/utils";
import { apiPost, apiPatch } from "@/lib/api";
import type { LeafCategory } from "../page";

interface BrandKitOption {
  id: string;
  name: string;
}

interface Props {
  leafCategories: LeafCategory[];
  brandKits: BrandKitOption[];
  token: string;
}

interface ProductRead {
  id: string;
}

const INPUT =
  "w-full mt-1 rounded-md border border-input bg-background px-3 py-1.5 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-60";

const LABEL = "text-xs text-muted-foreground";

export function UploadForm({ leafCategories, brandKits, token }: Props) {
  const router = useRouter();

  const [submitting, setSubmitting] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form fields
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [color, setColor] = useState("");
  const [material, setMaterial] = useState("");
  const [sizeRange, setSizeRange] = useState("");
  const [brandKitId, setBrandKitId] = useState("");

  const inputRef = useRef<HTMLInputElement>(null);

  const pickFile = useCallback((f: File) => {
    if (!f.type.startsWith("image/")) return;
    setFile(f);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target?.result as string);
    reader.readAsDataURL(f);
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const dropped = e.dataTransfer.files[0];
      if (dropped) pickFile(dropped);
    },
    [pickFile]
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!code.trim()) { setError("SKU code is required."); return; }
    if (!name.trim()) { setError("Product name is required."); return; }
    if (!file) { setError("Please select a garment photo."); return; }

    setSubmitting(true);
    try {
      const attributes: Record<string, string> = {};
      if (material.trim()) attributes.material = material.trim();
      if (sizeRange.trim()) attributes.size_range = sizeRange.trim();

      const product = await apiPost<ProductRead>(
        "/api/v1/products",
        {
          code: code.trim(),
          name: name.trim(),
          category_id: categoryId || null,
          brand_kit_id: brandKitId || null,
          color: color.trim() || null,
          attributes,
        },
        token ?? undefined
      );

      const { url, key } = await apiPost<{ url: string; key: string }>(
        `/api/v1/products/${product.id}/upload-url`,
        {},
        token ?? undefined
      );

      const uploadRes = await fetch(url, {
        method: "PUT",
        body: file,
        headers: { "Content-Type": file.type },
      });
      if (!uploadRes.ok) throw new Error("Image upload failed");

      await apiPatch(
        `/api/v1/products/${product.id}`,
        { source_image_key: key },
        token ?? undefined
      );

      router.push(`/app/products/${product.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="grid grid-cols-2 gap-4">
        {/* ── Left: Garment photo ─────────────────────────────────── */}
        <div className="rounded-lg border bg-card p-4">
          <p className="text-sm font-medium mb-2.5">Garment photo</p>

          <div
            role="button"
            tabIndex={0}
            onClick={() => inputRef.current?.click()}
            onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            style={{ height: 220 }}
            className={cn(
              "flex flex-col items-center justify-center rounded-md border border-dashed cursor-pointer transition-colors bg-muted/40 overflow-hidden",
              dragging && "border-primary bg-accent",
              !dragging && "hover:border-primary/50",
              submitting && "pointer-events-none opacity-60"
            )}
          >
            {preview ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={preview}
                alt="preview"
                className="h-full w-full object-contain"
              />
            ) : (
              <div className="flex flex-col items-center gap-1.5 text-center px-4">
                <Upload className="h-6 w-6 text-muted-foreground" />
                <p className="text-sm text-muted-foreground">
                  Drop image here or click to browse
                </p>
                <p className="text-xs text-muted-foreground/70">
                  JPG, PNG, WEBP up to 20 MB
                </p>
              </div>
            )}
          </div>
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => { const f = e.target.files?.[0]; if (f) pickFile(f); }}
            disabled={submitting}
          />
          <p className="text-xs text-muted-foreground mt-2.5">
            Tip: a flatlay on white with no shadows produces the cleanest on-model output.
          </p>
        </div>

        {/* ── Right: Attributes ─────────────────────────────────────── */}
        <div className="rounded-lg border bg-card p-4">
          <p className="text-sm font-medium mb-2.5">Attributes</p>

          <div className="grid gap-2.5">
            <div>
              <label className={LABEL} htmlFor="sku-name">Product name</label>
              <input
                id="sku-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Floral wrap dress"
                className={INPUT}
                disabled={submitting}
              />
            </div>

            <div>
              <label className={LABEL} htmlFor="sku-code">SKU code</label>
              <input
                id="sku-code"
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="SS26-T-014"
                className={INPUT}
                disabled={submitting}
              />
            </div>

            <div>
              <label className={LABEL} htmlFor="garment-type">Garment type</label>
              <select
                id="garment-type"
                value={categoryId}
                onChange={(e) => setCategoryId(e.target.value)}
                className={INPUT}
                disabled={submitting}
              >
                <option value="">— select —</option>
                {leafCategories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.display_name}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              <div>
                <label className={LABEL} htmlFor="color">Color</label>
                <input
                  id="color"
                  type="text"
                  value={color}
                  onChange={(e) => setColor(e.target.value)}
                  placeholder="Sage green"
                  className={INPUT}
                  disabled={submitting}
                />
              </div>
              <div>
                <label className={LABEL} htmlFor="material">Material</label>
                <input
                  id="material"
                  type="text"
                  value={material}
                  onChange={(e) => setMaterial(e.target.value)}
                  placeholder="100% linen"
                  className={INPUT}
                  disabled={submitting}
                />
              </div>
            </div>

            <div>
              <label className={LABEL} htmlFor="size-range">Size range</label>
              <input
                id="size-range"
                type="text"
                value={sizeRange}
                onChange={(e) => setSizeRange(e.target.value)}
                placeholder="XS, S, M, L, XL"
                className={INPUT}
                disabled={submitting}
              />
            </div>

            {brandKits.length > 0 && (
              <div>
                <label className={LABEL} htmlFor="brand-kit">Brand kit</label>
                <select
                  id="brand-kit"
                  value={brandKitId}
                  onChange={(e) => setBrandKitId(e.target.value)}
                  className={INPUT}
                  disabled={submitting}
                >
                  <option value="">— none —</option>
                  {brandKits.map((k) => (
                    <option key={k.id} value={k.id}>
                      {k.name}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </div>
      </div>

      {error && (
        <p className="text-sm text-destructive mt-3">{error}</p>
      )}

      <div className="flex justify-end mt-4">
        <button
          type="submit"
          disabled={submitting}
          className="inline-flex items-center justify-center rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium hover:bg-primary/90 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
        >
          {submitting ? "Saving…" : "Save and generate"}
        </button>
      </div>
    </form>
  );
}
