"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Upload } from "lucide-react";
import { apiPost, apiPatch } from "@/lib/api";
import { compressImage } from "@/lib/compress-image";

interface Props {
  productId: string;
  token: string;
}

export function ImageUploader({ productId, token }: Props) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = async (file: File) => {
    if (!file.type.startsWith("image/")) return;
    setError(null);
    setUploading(true);
    try {
      const { base64, mediaType } = await compressImage(file);
      const { key } = await apiPost<{ url: string; key: string }>(
        `/api/v1/products/${productId}/upload?view=front`,
        { image_b64: base64, media_type: mediaType },
        token
      );
      await apiPatch(`/api/v1/products/${productId}`, { source_image_key: key }, token);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="h-full flex flex-col items-center justify-center gap-3">
      <button
        onClick={() => inputRef.current?.click()}
        disabled={uploading}
        className="inline-flex items-center gap-2 rounded-full bg-foreground text-background px-5 py-2.5 text-sm font-medium hover:opacity-80 disabled:opacity-40 transition-opacity"
      >
        <Upload className="h-3.5 w-3.5" />
        {uploading ? "Uploading…" : "Upload image"}
      </button>
      <p className="text-xs text-muted-foreground">Flatlay or mannequin photo</p>
      {error && <p className="text-xs text-destructive max-w-xs text-center">{error}</p>}
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
      />
    </div>
  );
}
