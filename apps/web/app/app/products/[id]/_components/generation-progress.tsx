"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

interface Props {
  productId: string;
  token: string;
}

export function GenerationProgress({ productId, token }: Props) {
  const router = useRouter();
  // Keep a stable ref so the effect doesn't re-run when router identity changes
  const routerRef = useRef(router);
  routerRef.current = router;

  const [jobStatuses, setJobStatuses] = useState<Record<string, string>>({});
  const [connected, setConnected] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    (async () => {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/products/${productId}/events`,
          {
            headers: { Authorization: `Bearer ${token}` },
            signal: ctrl.signal,
          }
        );
        if (!res.ok || !res.body) return;

        setConnected(true);
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buf = "";
        let eventType = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done || ctrl.signal.aborted) break;

          buf += decoder.decode(value, { stream: true });
          const lines = buf.split("\n");
          buf = lines.pop() ?? "";

          for (const line of lines) {
            if (line.startsWith("event: ")) {
              eventType = line.slice(7).trim();
            } else if (line.startsWith("data: ") && eventType) {
              try {
                const data = JSON.parse(line.slice(6));
                if (eventType === "job_status" && data.job_id) {
                  setJobStatuses((prev) => ({ ...prev, [data.job_id]: data.status }));
                } else if (eventType === "done") {
                  ctrl.abort();
                  routerRef.current.refresh();
                  return;
                }
              } catch {
                // ignore parse errors
              }
              eventType = "";
            } else if (line === "") {
              eventType = "";
            }
          }
        }
      } catch (err: unknown) {
        if (err instanceof Error && err.name !== "AbortError") {
          // Single refresh attempt on connection error — no retry loop
          routerRef.current.refresh();
        }
      }
    })();

    return () => ctrl.abort();
  }, [productId, token]); // router intentionally excluded — use routerRef

  const statuses = Object.values(jobStatuses);
  // Backend enqueues 9 image jobs + 1 video job; use actual count once known
  const total = statuses.length || 10;
  const done = statuses.filter((s) => s === "succeeded" || s === "failed").length;
  const pct = Math.round((done / total) * 100);
  const minPct = connected ? 4 : 0;

  return (
    <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-amber-800">
          {!connected
            ? "Starting generation agent…"
            : done === 0
            ? "Generating on-model images…"
            : `${done} of ${total} complete`}
        </p>
        {connected && (
          <span className="text-xs text-amber-600 tabular-nums">{pct}%</span>
        )}
      </div>
      <div className="h-1.5 rounded-full bg-amber-200 overflow-hidden">
        <div
          className="h-full rounded-full bg-amber-500 transition-all duration-700"
          style={{ width: `${Math.max(pct, minPct)}%` }}
        />
      </div>
    </div>
  );
}
