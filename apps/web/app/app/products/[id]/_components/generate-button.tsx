"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiPost } from "@/lib/api";

interface Props {
  productId: string;
  canGenerate: boolean;
  token: string;
}

export function GenerateButton({ productId, canGenerate, token }: Props) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    setError(null);
    setLoading(true);
    try {
      await apiPost(`/api/v1/products/${productId}/generate`, {}, token);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        onClick={handleGenerate}
        disabled={!canGenerate || loading}
        className="inline-flex items-center justify-center rounded-full bg-foreground text-background px-5 py-2 text-sm font-medium hover:opacity-80 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity"
      >
        {loading ? "Queuing…" : "Generate →"}
      </button>
      {error && <p className="text-xs text-destructive max-w-xs text-right">{error}</p>}
    </div>
  );
}
