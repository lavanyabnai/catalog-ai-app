export default function Home() {
  return (
    <div className="min-h-screen bg-white dark:bg-gray-950 font-[family-name:var(--font-geist-sans)]">
      {/* Nav */}
      <nav className="border-b border-gray-100 dark:border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md bg-gray-900 dark:bg-white flex items-center justify-center">
            <span className="text-white dark:text-gray-900 text-xs font-bold">C</span>
          </div>
          <span className="font-semibold text-gray-900 dark:text-white text-sm tracking-tight">
            catalog<span className="text-gray-400">-ai</span>
          </span>
        </div>
        <div className="flex items-center gap-3">
          <a
            href="/dashboard"
            className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
          >
            Dashboard
          </a>
          <a
            href="/upload"
            className="text-sm bg-gray-900 dark:bg-white text-white dark:text-gray-900 px-4 py-2 rounded-full hover:opacity-80 transition-opacity"
          >
            Get started
          </a>
        </div>
      </nav>

      {/* Hero */}
      <main className="max-w-4xl mx-auto px-6 pt-24 pb-20 text-center">
        <div className="inline-flex items-center gap-2 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 text-xs px-3 py-1.5 rounded-full mb-8">
          <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
          AI-powered catalog generation
        </div>

        <h1 className="text-5xl sm:text-6xl font-bold text-gray-900 dark:text-white leading-tight tracking-tight mb-6">
          Turn products into
          <br />
          <span className="text-gray-400">stunning catalogs</span>
        </h1>

        <p className="text-lg text-gray-500 dark:text-gray-400 max-w-xl mx-auto mb-10 leading-relaxed">
          Upload your product images and let AI generate professional catalog
          photos and videos — ready for e-commerce in minutes.
        </p>

        <div className="flex items-center justify-center gap-3 flex-wrap">
          <a
            href="/upload"
            className="bg-gray-900 dark:bg-white text-white dark:text-gray-900 px-6 py-3 rounded-full text-sm font-medium hover:opacity-80 transition-opacity"
          >
            Upload products
          </a>
          <a
            href="/dashboard"
            className="border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 px-6 py-3 rounded-full text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
          >
            View dashboard
          </a>
        </div>
      </main>

      {/* Features */}
      <section className="max-w-4xl mx-auto px-6 pb-24">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            {
              icon: "↑",
              title: "Batch upload",
              desc: "Upload dozens of product images at once and process them in parallel.",
            },
            {
              icon: "✦",
              title: "AI generation",
              desc: "Generate on-model images and short video clips powered by fal.ai.",
            },
            {
              icon: "⬇",
              title: "Export ready",
              desc: "Download catalog-ready assets optimised for your storefront.",
            },
          ].map((f) => (
            <div
              key={f.title}
              className="border border-gray-100 dark:border-gray-800 rounded-2xl p-6 bg-gray-50 dark:bg-gray-900"
            >
              <div className="text-2xl mb-3">{f.icon}</div>
              <h3 className="font-semibold text-gray-900 dark:text-white text-sm mb-1">
                {f.title}
              </h3>
              <p className="text-gray-500 dark:text-gray-400 text-sm leading-relaxed">
                {f.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 dark:border-gray-800 px-6 py-6 text-center text-xs text-gray-400 dark:text-gray-600">
        catalog-ai &mdash; AI catalog generation for fashion retailers
      </footer>
    </div>
  );
}
