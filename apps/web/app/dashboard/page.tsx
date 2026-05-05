const stats = [
  { label: "SKUs live", value: "847" },
  { label: "In generation", value: "23" },
  { label: "Awaiting review", value: "12" },
  { label: "GPU spend (mo)", value: "$284" },
];

const activity = [
  { text: "Ingestion agent picked up 5 SKUs from supplier feed", time: "2m" },
  { text: "Generation agent finished bundle for SKU SS26-T-014", time: "8m" },
  { text: "Channel agent published 3 SKUs to Amazon and TikTok", time: "22m" },
  { text: "Optimization agent flagged SKU SS26-D-003 for refresh", time: "1h" },
];

export default function DashboardPage() {
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
          href="/upload"
          className="text-sm bg-gray-900 dark:bg-white text-white dark:text-gray-900 px-4 py-2 rounded-full hover:opacity-80 transition-opacity"
        >
          + new SKU
        </a>
      </nav>

      {/* Content */}
      <div className="max-w-5xl mx-auto px-6 pt-10 pb-20">
        {/* Page header */}
        <div className="mb-6">
          <h1 className="text-lg font-medium text-gray-900 dark:text-white">Catalog workspace</h1>
          <p className="text-sm text-gray-400 dark:text-gray-500 mt-0.5">
            Acme apparel · spring 26 collection
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          {stats.map((s) => (
            <div
              key={s.label}
              className="bg-gray-50 dark:bg-gray-900 rounded-xl px-4 py-4"
            >
              <p className="text-xs text-gray-400 dark:text-gray-500">{s.label}</p>
              <p className="text-2xl font-medium text-gray-900 dark:text-white mt-1">{s.value}</p>
            </div>
          ))}
        </div>

        {/* Main grid */}
        <div className="grid grid-cols-1 sm:grid-cols-[1.4fr_1fr] gap-4">
          {/* Agent activity */}
          <div className="border border-gray-100 dark:border-gray-800 rounded-2xl px-5 py-4 bg-gray-50 dark:bg-gray-900">
            <p className="text-sm font-medium text-gray-900 dark:text-white mb-3">Agent activity</p>
            <div className="flex flex-col">
              {activity.map((a, i) => (
                <div
                  key={i}
                  className={`flex items-start justify-between gap-4 py-3 text-sm ${
                    i < activity.length - 1
                      ? "border-b border-gray-100 dark:border-gray-800"
                      : ""
                  }`}
                >
                  <span className="text-gray-600 dark:text-gray-300 leading-snug">{a.text}</span>
                  <span className="text-xs text-gray-300 dark:text-gray-600 whitespace-nowrap pt-0.5">
                    {a.time}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Needs attention */}
          <div className="border border-gray-100 dark:border-gray-800 rounded-2xl px-5 py-4 bg-gray-50 dark:bg-gray-900">
            <p className="text-sm font-medium text-gray-900 dark:text-white mb-3">Needs your attention</p>
            <div className="flex flex-col gap-3">
              <div className="bg-amber-50 dark:bg-amber-950/40 rounded-xl px-4 py-3">
                <p className="text-sm font-medium text-amber-700 dark:text-amber-400">
                  12 SKUs ready to review
                </p>
                <p className="text-xs text-amber-500 dark:text-amber-500 mt-0.5">
                  Spring linen capsule
                </p>
              </div>
              <div className="bg-blue-50 dark:bg-blue-950/40 rounded-xl px-4 py-3">
                <p className="text-sm font-medium text-blue-700 dark:text-blue-400">
                  A/B test result available
                </p>
                <p className="text-xs text-blue-500 dark:text-blue-500 mt-0.5">
                  SS26-T-008 winner picked
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
