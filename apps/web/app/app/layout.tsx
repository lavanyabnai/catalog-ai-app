import Link from "next/link";
import { SignOutButton } from "./_components/sign-out-button";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-background">
      <header className="bg-white border-b border-border sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 flex h-14 items-center justify-between">
          <nav className="flex items-center gap-8">
            <Link href="/app" className="font-bold text-sm tracking-tight text-foreground">
              catalog-ai
            </Link>
            <Link
              href="/app"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Overview
            </Link>
            <Link
              href="/app/catalog"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Catalog
            </Link>
            <Link
              href="/app/tryon"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Try On
            </Link>
            <Link
              href="/app/new"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              New SKU
            </Link>
          </nav>
          <SignOutButton />
        </div>
      </header>
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-8">{children}</main>
    </div>
  );
}
