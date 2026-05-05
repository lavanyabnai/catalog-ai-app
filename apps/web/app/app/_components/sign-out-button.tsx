"use client";

import { useRouter } from "next/navigation";

export function SignOutButton() {
  const router = useRouter();

  const signOut = () => {
    document.cookie = "session_token=; path=/; max-age=0; SameSite=Lax";
    router.push("/sign-in");
  };

  return (
    <button
      onClick={signOut}
      className="text-sm text-muted-foreground hover:text-foreground transition-colors"
    >
      Sign out
    </button>
  );
}
