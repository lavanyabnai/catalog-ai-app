import { Sparkles } from "lucide-react";
import { getToken } from "@/lib/auth";
import { TryOnStudio } from "./_components/tryon-studio";

export default async function TryOnPage() {
  const token = await getToken();

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="rounded-xl border border-border bg-gradient-to-r from-violet-50 to-pink-50 dark:from-violet-950/20 dark:to-pink-950/20 px-6 py-5">
        <div className="flex items-start gap-3">
          <div className="rounded-lg bg-gradient-to-br from-violet-500 to-pink-500 p-2 text-white shadow-sm">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold">Virtual Try-On</h1>
            <p className="mt-0.5 text-sm text-muted-foreground">
              Select a person photo and a garment image — AI places the garment on the model in seconds.
            </p>
            <div className="mt-2 flex flex-wrap gap-3 text-xs text-muted-foreground">
              <span className="inline-flex items-center gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-violet-400" />
                Powered by Kolors Virtual Try-On
              </span>
              <span className="inline-flex items-center gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                Results in 30–60 s
              </span>
              <span className="inline-flex items-center gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
                Works with ethnic &amp; western styles
              </span>
            </div>
          </div>
        </div>
      </div>

      <TryOnStudio token={token} />
    </div>
  );
}
