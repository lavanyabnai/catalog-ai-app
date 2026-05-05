"use client";

import type { JobRead } from "../page";

interface Persona {
  id: string;
  display_name: string;
  ethnicity: string;
  body_type: string;
  height_cm: number;
}

interface Props {
  jobs: JobRead[];
  personas: Persona[];
}

export function LeftRail({ jobs, personas }: Props) {
  // Deduplicate personas used in this bundle
  const seen = new Set<string>();
  const usedPersonas: Array<{
    id: string;
    display_name: string;
    ethnicity: string;
    body_type: string;
    height_cm: number;
    jobCount: number;
  }> = [];

  for (const job of jobs) {
    const p = job.prompt.persona;
    if (!p) continue;
    if (seen.has(p.id)) {
      const existing = usedPersonas.find((u) => u.id === p.id);
      if (existing) existing.jobCount++;
    } else {
      seen.add(p.id);
      // Merge with full persona data if available
      const full = personas.find((x) => x.id === p.id);
      usedPersonas.push({
        id: p.id,
        display_name: full?.display_name ?? p.display_name ?? p.id,
        ethnicity: full?.ethnicity ?? p.ethnicity ?? "",
        body_type: full?.body_type ?? p.body_type ?? "",
        height_cm: full?.height_cm ?? p.height_cm ?? 0,
        jobCount: 1,
      });
    }
  }

  return (
    <aside className="w-[200px] shrink-0 border-r overflow-y-auto p-3 space-y-3">
      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
        Models
      </p>

      {usedPersonas.length === 0 ? (
        <p className="text-xs text-muted-foreground">No personas</p>
      ) : (
        usedPersonas.map((p) => (
          <div key={p.id} className="rounded-md border p-2 space-y-0.5">
            <p className="text-xs font-medium truncate">{p.display_name}</p>
            <p className="text-[10px] text-muted-foreground">{p.ethnicity}</p>
            <p className="text-[10px] text-muted-foreground">{p.body_type}</p>
            {p.height_cm > 0 && (
              <p className="text-[10px] text-muted-foreground">{p.height_cm} cm</p>
            )}
            <p className="text-[10px] text-muted-foreground">{p.jobCount} shot{p.jobCount !== 1 ? "s" : ""}</p>
          </div>
        ))
      )}

      {jobs.length > 0 && (
        <>
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide pt-2">
            Poses
          </p>
          <div className="flex flex-wrap gap-1">
            {Array.from(new Set(jobs.map((j) => j.prompt.pose).filter(Boolean))).map(
              (pose) => (
                <span
                  key={pose}
                  className="text-[10px] bg-muted rounded px-1.5 py-0.5 capitalize"
                >
                  {pose}
                </span>
              )
            )}
          </div>
        </>
      )}
    </aside>
  );
}
