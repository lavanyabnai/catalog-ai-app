export default function Home() {
  return (
    <div className="min-h-screen bg-white font-[family-name:var(--font-geist-sans)] text-gray-900">

      {/* ── Nav ─────────────────────────────────────────────────── */}
      <nav className="sticky top-0 z-20 bg-white/80 backdrop-blur border-b border-gray-100 px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gray-900 flex items-center justify-center">
            <span className="text-white text-xs font-bold">C</span>
          </div>
          <span className="font-semibold text-sm tracking-tight">
            catalog<span className="text-gray-400">-ai</span>
          </span>
        </div>
        <div className="hidden sm:flex items-center gap-7 text-sm text-gray-500">
          <a href="#how-it-works" className="hover:text-gray-900 transition-colors">How it works</a>
          <a href="#features" className="hover:text-gray-900 transition-colors">Features</a>
          <a href="#outputs" className="hover:text-gray-900 transition-colors">Outputs</a>
        </div>
        <div className="flex items-center gap-2.5">
          <a
            href="/app"
            className="text-sm bg-gray-900 text-white px-4 py-2 rounded-full hover:opacity-80 transition-opacity font-medium"
          >
            Open app
          </a>
        </div>
      </nav>

      {/* ── Hero ─────────────────────────────────────────────────── */}
      <section className="max-w-5xl mx-auto px-6 pt-20 pb-16 text-center">
        <div className="inline-flex items-center gap-2 bg-gray-50 border border-gray-200 text-gray-600 text-xs px-3.5 py-1.5 rounded-full mb-8 font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          AI Catalog Fashion Photo Generator
        </div>

        <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold leading-[1.08] tracking-tight mb-6">
          Generate catalog-ready
          <br />
          <span className="text-gray-400">on-model fashion photos</span>
        </h1>

        <p className="text-lg text-gray-500 max-w-2xl mx-auto mb-4 leading-relaxed">
          Upload a garment flatlay — our AI places it on diverse models, generates
          studio-quality catalog images and video clips, ready for your storefront
          in minutes.
        </p>

        <p className="text-sm text-gray-400 mb-10">
          From <span className="font-semibold text-gray-700">₹5 / image</span> &nbsp;·&nbsp; Results in <span className="font-semibold text-gray-700">30–40 seconds</span>
        </p>

        <div className="flex items-center justify-center gap-3 flex-wrap">
          <a
            href="/app"
            className="bg-gray-900 text-white px-7 py-3 rounded-full text-sm font-semibold hover:opacity-85 transition-opacity"
          >
            Generate →
          </a>
          <a
            href="/app/catalog"
            className="border border-gray-200 text-gray-700 px-7 py-3 rounded-full text-sm font-medium hover:bg-gray-50 transition-colors"
          >
            Explore styles
          </a>
        </div>
      </section>

      {/* ── Hero visual strip ─────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 pb-20">
        <div className="grid grid-cols-4 gap-3 rounded-3xl overflow-hidden">
          {[
            { img: "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=600&q=80", label: "Kurta · Studio" },
            { img: "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=600&q=80", label: "Saree · Editorial" },
            { img: "https://images.unsplash.com/photo-1617627143750-d86bc21e42bb?w=600&q=80", label: "Lehenga · PDP" },
            { img: "https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=600&q=80", label: "Dress · Marketplace" },
          ].map((item, i) => (
            <div key={i} className="aspect-[3/4] rounded-2xl overflow-hidden relative">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={item.img} alt={item.label} className="w-full h-full object-cover" />
              <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
              <span className="absolute bottom-3 left-3 text-[10px] text-white/90 font-medium">
                {item.label}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* ── How it works ─────────────────────────────────────────── */}
      <section id="how-it-works" className="bg-gray-50 py-20 px-6">
        <div className="max-w-5xl mx-auto">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest text-center mb-3">How it works</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-center mb-14 tracking-tight">
            Three steps to catalog-ready
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            {[
              {
                step: "01",
                title: "Upload your garment",
                desc: "Drop a flatlay or mannequin photo — front, back, and detail views. Our AI auto-fills product name, color, material, and category.",
                icon: "↑",
              },
              {
                step: "02",
                title: "Set your controls",
                desc: "Choose model persona, pose, scene, and output format. Mix ethnic and western styles across diverse model profiles.",
                icon: "✦",
              },
              {
                step: "03",
                title: "Download & publish",
                desc: "Get catalog-ready images and video clips — PDP, marketplace, editorial, and social formats — in under a minute.",
                icon: "⬇",
              },
            ].map((s) => (
              <div key={s.step} className="bg-white rounded-2xl p-7 border border-gray-100">
                <div className="flex items-center gap-3 mb-5">
                  <span className="text-xs font-bold text-gray-300 font-mono">{s.step}</span>
                  <span className="text-xl">{s.icon}</span>
                </div>
                <h3 className="font-semibold text-base mb-2">{s.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ─────────────────────────────────────────────── */}
      <section id="features" className="py-20 px-6">
        <div className="max-w-5xl mx-auto">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest text-center mb-3">Features</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-center mb-14 tracking-tight">
            Built for fashion retailers
          </h2>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            {[
              { title: "AI auto-fill", desc: "Claude vision reads garment type, color, and material from your photo instantly." },
              { title: "Multi-view upload", desc: "Front, back, and detail shots for the most accurate on-model generation." },
              { title: "Diverse models", desc: "8 system personas across body types, ethnicities, and gender presentations." },
              { title: "Ethnic wear ready", desc: "Kurtas, sarees, lehengas, salwar kameez — full Indian ethnic category support." },
              { title: "Video clips", desc: "Short on-model video loops generated alongside still images, no extra work." },
              { title: "Studio & review", desc: "Approve hero images, manage bundles, and track generation in one workspace." },
            ].map((f) => (
              <div key={f.title} className="border border-gray-100 rounded-2xl p-5 hover:border-gray-300 transition-colors">
                <h3 className="font-semibold text-sm mb-1.5">{f.title}</h3>
                <p className="text-xs text-gray-500 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Outputs ──────────────────────────────────────────────── */}
      <section id="outputs" className="bg-gray-50 py-20 px-6">
        <div className="max-w-5xl mx-auto">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest text-center mb-3">Outputs</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-center mb-4 tracking-tight">
            Every format you need
          </h2>
          <p className="text-center text-gray-500 text-sm mb-12 max-w-xl mx-auto">
            One upload generates images and video optimised for PDP, marketplace listings, social, and editorial use.
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: "PDP", ratio: "aspect-[3/4]", bg: "bg-stone-100" },
              { label: "Marketplace", ratio: "aspect-square", bg: "bg-amber-50" },
              { label: "Editorial", ratio: "aspect-[3/4]", bg: "bg-rose-50" },
              { label: "Video clip", ratio: "aspect-[9/16]", bg: "bg-sky-50" },
            ].map((o) => (
              <div key={o.label} className="flex flex-col gap-2">
                <div className={`${o.bg} ${o.ratio} rounded-2xl flex items-center justify-center`}>
                  <span className="text-gray-300 text-xs font-medium">{o.label}</span>
                </div>
                <p className="text-xs font-medium text-center text-gray-500">{o.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────────── */}
      <section className="py-24 px-6 text-center">
        <h2 className="text-4xl sm:text-5xl font-bold tracking-tight mb-5">
          Ready to launch your catalog?
        </h2>
        <p className="text-gray-500 text-base mb-10 max-w-lg mx-auto">
          Create an account and generate your first on-model image in under 2 minutes.
        </p>
        <div className="flex items-center justify-center gap-3">
          <a
            href="/app"
            className="bg-gray-900 text-white px-8 py-3.5 rounded-full text-sm font-semibold hover:opacity-85 transition-opacity"
          >
            Get started free →
          </a>
          <a
            href="/app"
            className="border border-gray-200 text-gray-700 px-8 py-3.5 rounded-full text-sm font-medium hover:bg-gray-50 transition-colors"
          >
            View dashboard
          </a>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────── */}
      <footer className="border-t border-gray-100 px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4 max-w-5xl mx-auto text-xs text-gray-400">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded bg-gray-900 flex items-center justify-center">
            <span className="text-white text-[9px] font-bold">C</span>
          </div>
          <span>catalog-ai — AI catalog generation for fashion retailers</span>
        </div>
        <div className="flex gap-5">
          <a href="/app" className="hover:text-gray-700 transition-colors">Sign in</a>
          <a href="/app" className="hover:text-gray-700 transition-colors">Sign up</a>
          <a href="/app" className="hover:text-gray-700 transition-colors">Dashboard</a>
        </div>
      </footer>
    </div>
  );
}
