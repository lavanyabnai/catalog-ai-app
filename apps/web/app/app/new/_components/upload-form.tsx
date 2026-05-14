"use client";

import { useRouter } from "next/navigation";
import { useCallback, useRef, useState } from "react";
import { Sparkles, Upload, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { apiPost, apiPatch } from "@/lib/api";
import { compressImage } from "@/lib/compress-image";
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

interface AnalyzeResponse {
  name?: string;
  color?: string;
  material?: string;
  category_hint?: string;
  size_range?: string;
}

type View = "front" | "back" | "detail";

const VIEWS: { key: View; label: string; hint: string }[] = [
  { key: "front", label: "Front view", hint: "Primary — required" },
  { key: "back",  label: "Back view",  hint: "Optional" },
  { key: "detail", label: "Detail / Side", hint: "Optional" },
];

const GARMENT_TYPES = [
  // Indian Ethnic — Women
  "Kurta",
  "Kurti",
  "Saree",
  "Lehenga",
  "Salwar Kameez",
  "Anarkali Suit",
  "Coord Set",
  "Dupatta / Stole",
  // Indian Ethnic — Men
  "Kurta (Men)",
  "Sherwani",
  "Nehru Jacket",
  "Dhoti / Lungi",
  // Western — Women
  "T-Shirt / Top",
  "Blouse / Shirt",
  "Dress",
  "Skirt",
  "Jeans (Women)",
  "Trousers / Palazzos",
  "Jacket / Coat (Women)",
  // Western — Men
  "T-Shirt (Men)",
  "Shirt (Men)",
  "Jeans (Men)",
  "Trousers / Chinos",
  "Jacket / Coat (Men)",
] as const;

const INPUT =
  "w-full mt-1 rounded-md border border-input bg-background px-3 py-1.5 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-60";

const LABEL = "text-xs text-muted-foreground";

function AiBadge() {
  return (
    <span className="inline-flex items-center gap-0.5 ml-1.5 rounded px-1 py-px text-[10px] font-medium bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-300">
      <Sparkles className="h-2.5 w-2.5" />
      AI
    </span>
  );
}


interface SlotProps {
  label: string;
  hint: string;
  file: File | null;
  preview: string | null;
  primary?: boolean;
  busy: boolean;
  onFile: (f: File) => void;
  onClear: () => void;
}

function PhotoSlot({ label, hint, file, preview, primary, busy, onFile, onClear }: SlotProps) {
  const [dragging, setDragging] = useState(false);
  const ref = useRef<HTMLInputElement>(null);

  const pick = useCallback(
    (f: File) => { if (f.type.startsWith("image/")) onFile(f); },
    [onFile]
  );

  return (
    <div>
      <div className="flex items-baseline justify-between mb-1">
        <p className="text-xs font-medium">{label}</p>
        <p className="text-[10px] text-muted-foreground">{hint}</p>
      </div>

      <div
        role="button"
        tabIndex={0}
        onClick={() => !file && ref.current?.click()}
        onKeyDown={(e) => e.key === "Enter" && !file && ref.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          const f = e.dataTransfer.files[0];
          if (f) pick(f);
        }}
        style={{ height: primary ? 200 : 112 }}
        className={cn(
          "relative flex flex-col items-center justify-center rounded-md border border-dashed transition-colors bg-muted/40 overflow-hidden",
          !file && !busy && "cursor-pointer hover:border-primary/50",
          dragging && "border-primary bg-accent",
          busy && "opacity-60 pointer-events-none",
          primary && !file && "border-primary/30"
        )}
      >
        {preview ? (
          <>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={preview} alt={label} className="h-full w-full object-contain" />
            {!busy && (
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); onClear(); }}
                className="absolute top-1.5 right-1.5 rounded-full bg-background/80 p-0.5 text-muted-foreground hover:text-foreground transition-colors"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </>
        ) : (
          <div className="flex flex-col items-center gap-1 text-center px-3">
            <Upload className="h-5 w-5 text-muted-foreground" />
            {primary && (
              <p className="text-xs text-muted-foreground">Drop or click to browse</p>
            )}
          </div>
        )}
      </div>

      <input
        ref={ref}
        type="file"
        accept="image/*"
        className="hidden"
        disabled={busy}
        onChange={(e) => { const f = e.target.files?.[0]; if (f) pick(f); }}
      />
    </div>
  );
}

export function UploadForm({ leafCategories, brandKits, token }: Props) {
  const router = useRouter();

  const [submitting, setSubmitting] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiFields, setAiFields] = useState<Set<string>>(new Set());

  // One file + preview per view
  const [files, setFiles] = useState<Record<View, File | null>>({ front: null, back: null, detail: null });
  const [previews, setPreviews] = useState<Record<View, string | null>>({ front: null, back: null, detail: null });

  // Form fields
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [garmentType, setGarmentType] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [color, setColor] = useState("");
  const [material, setMaterial] = useState("");
  const [sizeRange, setSizeRange] = useState("");
  const [brandKitId, setBrandKitId] = useState("");

  const clearAiField = (field: string) =>
    setAiFields((prev) => { const s = new Set(prev); s.delete(field); return s; });

  const runAnalysis = useCallback(
    async (f: File) => {
      if (!token) return;
      setAnalyzing(true);
      try {
        const { base64: image_b64, mediaType: media_type } = await compressImage(f);
        const result = await apiPost<AnalyzeResponse>(
          "/api/v1/products/analyze-image",
          { image_b64, media_type },
          token
        );
        const filled = new Set<string>();
        if (result.name)      { setName(result.name);           filled.add("name"); }
        if (result.color)     { setColor(result.color);         filled.add("color"); }
        if (result.material)  { setMaterial(result.material);   filled.add("material"); }
        if (result.size_range){ setSizeRange(result.size_range);filled.add("sizeRange"); }
        if (result.category_hint) {
          const hint = result.category_hint.toLowerCase();
          // Match against the hardcoded garment type list
          const typeMatch = GARMENT_TYPES.find(
            (t) => t.toLowerCase().includes(hint) || hint.includes(t.toLowerCase().split(" ")[0])
          );
          if (typeMatch) { setGarmentType(typeMatch); filled.add("garmentType"); }
          // Also try to match the DB category tree if loaded
          if (leafCategories.length > 0) {
            const match = leafCategories.find(
              (c) =>
                c.display_name.toLowerCase().includes(hint) ||
                hint.includes(c.display_name.toLowerCase()) ||
                c.path.toLowerCase().includes(hint)
            );
            if (match) { setCategoryId(match.id); filled.add("categoryId"); }
          }
        }
        setAiFields(filled);
      } catch {
        // best-effort
      } finally {
        setAnalyzing(false);
      }
    },
    [token, leafCategories]
  );

  const handleFile = useCallback(
    (view: View, f: File) => {
      setFiles((prev) => ({ ...prev, [view]: f }));
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreviews((prev) => ({ ...prev, [view]: e.target?.result as string }));
      };
      reader.readAsDataURL(f);
      if (view === "front") runAnalysis(f);
    },
    [runAnalysis]
  );

  const clearFile = useCallback((view: View) => {
    setFiles((prev) => ({ ...prev, [view]: null }));
    setPreviews((prev) => ({ ...prev, [view]: null }));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!code.trim())    { setError("SKU code is required.");         return; }
    if (!name.trim())    { setError("Product name is required.");      return; }
    if (!files.front)    { setError("Front view photo is required."); return; }

    setSubmitting(true);
    try {
      const attributes: Record<string, unknown> = {};
      if (garmentType)      attributes.garment_type = garmentType;
      if (material.trim())  attributes.material     = material.trim();
      if (sizeRange.trim()) attributes.size_range   = sizeRange.trim();

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
        token
      );

      // Upload each filled view slot via Cloudinary (through API)
      const uploadedKeys: Partial<Record<View, string>> = {};
      for (const view of (["front", "back", "detail"] as View[])) {
        const f = files[view];
        if (!f) continue;
        const { base64: image_b64, mediaType: media_type } = await compressImage(f);
        const { key } = await apiPost<{ url: string; key: string }>(
          `/api/v1/products/${product.id}/upload?view=${view}`,
          { image_b64, media_type },
          token
        );
        uploadedKeys[view] = key;
      }

      const extraKeys = (["back", "detail"] as View[])
        .map((v) => uploadedKeys[v])
        .filter(Boolean) as string[];

      await apiPatch(
        `/api/v1/products/${product.id}`,
        {
          source_image_key: uploadedKeys.front,
          attributes: {
            ...attributes,
            ...(extraKeys.length ? { extra_image_keys: extraKeys } : {}),
          },
        },
        token
      );

      // Kick off generation immediately — don't wait, redirect to product page
      apiPost(`/api/v1/products/${product.id}/generate`, {}, token).catch(() => {
        // Non-fatal: user can retry from the product page
      });

      router.push(`/app/products/${product.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setSubmitting(false);
    }
  };

  const busy = submitting || analyzing;

  return (
    <form onSubmit={handleSubmit}>
      <div className="grid grid-cols-2 gap-4">
        {/* ── Left: Photo slots ────────────────────────────────────── */}
        <div className="rounded-lg border bg-card p-4">
          <div className="flex items-center justify-between mb-2.5">
            <p className="text-sm font-medium">Garment photos</p>
            {analyzing && (
              <p className="text-xs text-violet-600 flex items-center gap-1">
                <Sparkles className="h-3 w-3 animate-pulse" />
                Analyzing…
              </p>
            )}
          </div>

          {/* Front — large primary slot */}
          <PhotoSlot
            {...VIEWS[0]}
            primary
            file={files.front}
            preview={previews.front}
            busy={busy}
            onFile={(f) => handleFile("front", f)}
            onClear={() => clearFile("front")}
          />

          {/* Back + Detail — two small slots side by side */}
          <div className="grid grid-cols-2 gap-2 mt-2">
            {VIEWS.slice(1).map(({ key: viewKey, ...rest }) => (
              <PhotoSlot
                key={viewKey}
                {...rest}
                file={files[viewKey]}
                preview={previews[viewKey]}
                busy={busy}
                onFile={(f) => handleFile(viewKey, f)}
                onClear={() => clearFile(viewKey)}
              />
            ))}
          </div>

          <p className="text-xs text-muted-foreground mt-2.5">
            Flatlay on white gives the cleanest on-model output. JPG, PNG, WEBP up to 20 MB.
          </p>
        </div>

        {/* ── Right: Attributes ─────────────────────────────────────── */}
        <div className="rounded-lg border bg-card p-4">
          <p className="text-sm font-medium mb-2.5">Attributes</p>

          <div className="grid gap-2.5">
            <div>
              <label className={LABEL} htmlFor="sku-name">
                Product name
                {aiFields.has("name") && <AiBadge />}
              </label>
              <input
                id="sku-name"
                type="text"
                value={name}
                onChange={(e) => { setName(e.target.value); clearAiField("name"); }}
                placeholder="e.g. Floral wrap dress"
                className={INPUT}
                disabled={busy}
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
                disabled={busy}
              />
            </div>

            <div>
              <label className={LABEL} htmlFor="garment-type">
                Garment type
                {aiFields.has("garmentType") && <AiBadge />}
              </label>
              <select
                id="garment-type"
                value={garmentType}
                onChange={(e) => { setGarmentType(e.target.value); clearAiField("garmentType"); }}
                className={INPUT}
                disabled={busy}
              >
                <option value="">— select —</option>
                <optgroup label="Indian Ethnic — Women">
                  {GARMENT_TYPES.slice(0, 8).map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </optgroup>
                <optgroup label="Indian Ethnic — Men">
                  {GARMENT_TYPES.slice(8, 12).map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </optgroup>
                <optgroup label="Western — Women">
                  {GARMENT_TYPES.slice(12, 19).map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </optgroup>
                <optgroup label="Western — Men">
                  {GARMENT_TYPES.slice(19).map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </optgroup>
              </select>
            </div>

            {leafCategories.length > 0 && (
              <div>
                <label className={LABEL} htmlFor="category">
                  Category
                  {aiFields.has("categoryId") && <AiBadge />}
                </label>
                <select
                  id="category"
                  value={categoryId}
                  onChange={(e) => { setCategoryId(e.target.value); clearAiField("categoryId"); }}
                  className={INPUT}
                  disabled={busy}
                >
                  <option value="">— select —</option>
                  {leafCategories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.display_name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="grid grid-cols-2 gap-2.5">
              <div>
                <label className={LABEL} htmlFor="color">
                  Color
                  {aiFields.has("color") && <AiBadge />}
                </label>
                <input
                  id="color"
                  type="text"
                  value={color}
                  onChange={(e) => { setColor(e.target.value); clearAiField("color"); }}
                  placeholder="Sage green"
                  className={INPUT}
                  disabled={busy}
                />
              </div>
              <div>
                <label className={LABEL} htmlFor="material">
                  Material
                  {aiFields.has("material") && <AiBadge />}
                </label>
                <input
                  id="material"
                  type="text"
                  value={material}
                  onChange={(e) => { setMaterial(e.target.value); clearAiField("material"); }}
                  placeholder="100% linen"
                  className={INPUT}
                  disabled={busy}
                />
              </div>
            </div>

            <div>
              <label className={LABEL} htmlFor="size-range">
                Size range
                {aiFields.has("sizeRange") && <AiBadge />}
              </label>
              <input
                id="size-range"
                type="text"
                value={sizeRange}
                onChange={(e) => { setSizeRange(e.target.value); clearAiField("sizeRange"); }}
                placeholder="XS, S, M, L, XL"
                className={INPUT}
                disabled={busy}
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
                  disabled={busy}
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
          disabled={busy}
          className="inline-flex items-center justify-center rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium hover:bg-primary/90 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
        >
          {submitting ? "Saving…" : analyzing ? "Analyzing…" : "Save and generate"}
        </button>
      </div>
    </form>
  );
}
