import Link from "next/link";
import { SignOutButton } from "./_components/sign-out-button";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b bg-white sticky top-0 z-10">
        <div className="container flex h-14 items-center justify-between">
          <nav className="flex items-center gap-6">
            <Link href="/app" className="font-semibold text-sm tracking-tight">
              catalog-ai
            </Link>
            <Link
              href="/app"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Products
            </Link>
          </nav>
          <SignOutButton />
        </div>
      </header>
      <main className="flex-1 container py-8">{children}</main>
    </div>
  );
}
