import { cookies } from "next/headers";

/** Read the session token from the request cookie (server components only). */
export async function getToken(): Promise<string> {
  const store = await cookies();
  return store.get("session_token")?.value ?? "";
}
