"use client";

import Link from "next/link";

export function SignOutButton() {
  return (
    <Link href="/" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
      Home
    </Link>
  );
}
