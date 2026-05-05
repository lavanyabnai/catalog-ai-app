"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";

type FormState = {
  sku: string;
  garmentType: string;
  color: string;
  material: string;
  sizeRange: string;
  brandKit: string;
};

const initialForm: FormState = {
  sku: "",
  garmentType: "Top — t-shirt",
  color: "",
  material: "",
  sizeRange: "",
  brandKit: "Acme — coastal aesthetic",
};

export default function UploadPage() {
  const router = useRouter();
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [form, setForm] = useState<FormState>(initialForm);
  const [errors, setErrors] = useState<{ file?: string; sku?: string }>({});
  const [submitting, setSubmitting] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) {
      setFile(dropped);
      setErrors((prev) => ({ ...prev, file: undefined }));
    }
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const picked = e.target.files?.[0];
    if (picked) {
      setFile(picked);
      setErrors((prev) => ({ ...prev, file: undefined }));
    }
  }

  function setField(key: keyof FormState, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }));
    if (key === "sku") setErrors((prev) => ({ ...prev, sku: undefined }));
  }

  function validate() {
    const next: typeof errors = {};
    if (!file) next.file = "A garment photo is required.";
    if (!form.sku.trim()) next.sku = "SKU code is required.";
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSubmit() {
    if (!validate()) return;
    setSubmitting(true);
    try {
      // TODO: replace with real API call
      // const body = new FormData();
      // body.append("file", file!);
      // Object.entries(form).forEach(([k, v]) => body.append(k, v));
      // await fetch("/api/skus", { method: "POST", body });
      await new Promise((r) => setTimeout(r, 1200)); // simulated latency
      router.push("/dashboard");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950 font-[family-name:var(--font-geist-sans)]">
      {/* Nav */}
      <nav className="border-b border-gray-100 dark:border-gray-800 px-6 py-4 flex items-center justify-between">
        <a href="/" className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md bg-gray-900 dark:bg-white flex items-center justify-center">
            <span className="text-white dark:text-gray-900 text-xs font-bold">C</span>
          </div>
          <span className="font-semibold text-gray-900 dark:text-white text-sm tracking-tight">
            catalog<span className="text-gray-400">-ai</span>
          </span>
        </a>
        <a
          href="/dashboard"
          className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
        >
          Dashboard
        </a>
      </nav>

      {/* Page header */}
      <div className="max-w-4xl mx-auto px-6 pt-10 pb-6 flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-lg font-medium text-gray-900 dark:text-white">Add new SKU</h1>
          <p className="text-sm text-gray-400 dark:text-gray-500 mt-0.5">
            Upload a flatlay or worn-on-mannequin photo
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button className="text-sm border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 px-4 py-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
            Bulk import CSV
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="text-sm bg-gray-900 dark:bg-white text-white dark:text-gray-900 px-4 py-2 rounded-lg hover:opacity-80 transition-opacity font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {submitting ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-white/30 dark:border-gray-900/30 border-t-white dark:border-t-gray-900 rounded-full animate-spin" />
                Queuing…
              </>
            ) : (
              "Save and generate"
            )}
          </button>
        </div>
      </div>

      {/* Form */}
      <div className="max-w-4xl mx-auto px-6 pb-20">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Left — image drop */}
          <div className="border border-gray-100 dark:border-gray-800 rounded-2xl p-5 bg-gray-50 dark:bg-gray-900">
            <p className="text-sm font-medium text-gray-900 dark:text-white mb-3">Garment photo</p>

            <div
              onClick={() => inputRef.current?.click()}
              onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
              className={`border border-dashed rounded-xl h-56 flex flex-col items-center justify-center gap-2 cursor-pointer transition-colors ${
                errors.file
                  ? "border-red-300 dark:border-red-700 bg-red-50 dark:bg-red-950/20"
                  : dragging
                  ? "border-gray-400 bg-gray-100 dark:bg-gray-800"
                  : "border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-950 hover:bg-gray-50 dark:hover:bg-gray-800"
              }`}
            >
              {file ? (
                <>
                  <div className="w-8 h-8 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center text-green-600 dark:text-green-400 text-sm">
                    ✓
                  </div>
                  <p className="text-sm text-gray-700 dark:text-gray-300 font-medium">{file.name}</p>
                  <p className="text-xs text-gray-400">{(file.size / 1024 / 1024).toFixed(1)} MB</p>
                </>
              ) : (
                <>
                  <div className="w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center text-gray-400 text-lg">
                    ↑
                  </div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Drop image here or click to browse</p>
                  <p className="text-xs text-gray-300 dark:text-gray-600">JPG, PNG, WEBP up to 20 MB</p>
                </>
              )}
            </div>
            <input
              ref={inputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
              onChange={handleFileChange}
            />
            {errors.file && (
              <p className="text-xs text-red-500 mt-2">{errors.file}</p>
            )}
            <p className="text-xs text-gray-300 dark:text-gray-600 mt-3 leading-relaxed">
              Tip: a flatlay on white with no shadows produces the cleanest on-model output.
            </p>
          </div>

          {/* Right — attributes */}
          <div className="border border-gray-100 dark:border-gray-800 rounded-2xl p-5 bg-gray-50 dark:bg-gray-900">
            <p className="text-sm font-medium text-gray-900 dark:text-white mb-4">Attributes</p>
            <div className="flex flex-col gap-4">
              <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-400 dark:text-gray-500">SKU code</label>
                <input
                  type="text"
                  placeholder="SS26-T-014"
                  value={form.sku}
                  onChange={(e) => setField("sku", e.target.value)}
                  className={`text-sm border rounded-lg px-3 py-2 bg-white dark:bg-gray-950 text-gray-900 dark:text-white placeholder-gray-300 dark:placeholder-gray-600 focus:outline-none focus:ring-1 ${
                    errors.sku
                      ? "border-red-300 dark:border-red-700 focus:ring-red-300"
                      : "border-gray-200 dark:border-gray-700 focus:ring-gray-300 dark:focus:ring-gray-600"
                  }`}
                />
                {errors.sku && (
                  <p className="text-xs text-red-500">{errors.sku}</p>
                )}
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-400 dark:text-gray-500">Garment type</label>
                <select
                  value={form.garmentType}
                  onChange={(e) => setField("garmentType", e.target.value)}
                  className="text-sm border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 bg-white dark:bg-gray-950 text-gray-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-gray-300 dark:focus:ring-gray-600"
                >
                  <option>Top — t-shirt</option>
                  <option>Top — blouse</option>
                  <option>Dress</option>
                  <option>Outerwear</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-xs text-gray-400 dark:text-gray-500">Color</label>
                  <input
                    type="text"
                    placeholder="Sage green"
                    value={form.color}
                    onChange={(e) => setField("color", e.target.value)}
                    className="text-sm border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 bg-white dark:bg-gray-950 text-gray-900 dark:text-white placeholder-gray-300 dark:placeholder-gray-600 focus:outline-none focus:ring-1 focus:ring-gray-300 dark:focus:ring-gray-600"
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs text-gray-400 dark:text-gray-500">Material</label>
                  <input
                    type="text"
                    placeholder="100% linen"
                    value={form.material}
                    onChange={(e) => setField("material", e.target.value)}
                    className="text-sm border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 bg-white dark:bg-gray-950 text-gray-900 dark:text-white placeholder-gray-300 dark:placeholder-gray-600 focus:outline-none focus:ring-1 focus:ring-gray-300 dark:focus:ring-gray-600"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-400 dark:text-gray-500">Size range</label>
                <input
                  type="text"
                  placeholder="XS, S, M, L, XL"
                  value={form.sizeRange}
                  onChange={(e) => setField("sizeRange", e.target.value)}
                  className="text-sm border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 bg-white dark:bg-gray-950 text-gray-900 dark:text-white placeholder-gray-300 dark:placeholder-gray-600 focus:outline-none focus:ring-1 focus:ring-gray-300 dark:focus:ring-gray-600"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-400 dark:text-gray-500">Brand kit</label>
                <select
                  value={form.brandKit}
                  onChange={(e) => setField("brandKit", e.target.value)}
                  className="text-sm border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 bg-white dark:bg-gray-950 text-gray-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-gray-300 dark:focus:ring-gray-600"
                >
                  <option>Acme — coastal aesthetic</option>
                  <option>Acme — minimal studio</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
