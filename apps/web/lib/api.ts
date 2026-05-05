const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchWithAuth(
  path: string,
  options: RequestInit & { token?: string } = {}
): Promise<Response> {
  const { token, ...rest } = options;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(rest.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE}${path}`, { ...rest, headers });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res;
}

export async function apiGet<T>(path: string, token?: string): Promise<T> {
  const res = await fetchWithAuth(path, { method: "GET", token });
  return res.json() as Promise<T>;
}

export async function apiPost<T>(
  path: string,
  body: unknown,
  token?: string
): Promise<T> {
  const res = await fetchWithAuth(path, {
    method: "POST",
    body: JSON.stringify(body),
    token,
  });
  return res.json() as Promise<T>;
}

export async function apiPatch<T>(
  path: string,
  body: unknown,
  token?: string
): Promise<T> {
  const res = await fetchWithAuth(path, {
    method: "PATCH",
    body: JSON.stringify(body),
    token,
  });
  return res.json() as Promise<T>;
}

export async function apiDelete<T>(path: string, token?: string): Promise<T> {
  const res = await fetchWithAuth(path, { method: "DELETE", token });
  return res.json() as Promise<T>;
}

/**
 * Open a fetch-based SSE stream (EventSource doesn't support Authorization headers).
 * Returns a cancel function — call it to tear down the stream.
 *
 * @param onEvent  called for each parsed event with (eventName, parsedData)
 * @param onDone   called when the server sends `event: done` or the stream closes
 * @param onError  called on network/parse errors
 */
export function openSSEStream(
  path: string,
  token: string,
  onEvent: (event: string, data: unknown) => void,
  onDone?: () => void,
  onError?: (err: Error) => void
): () => void {
  let cancelled = false;

  async function connect() {
    let res: Response;
    try {
      res = await fetch(`${API_BASE}${path}`, {
        headers: { Authorization: `Bearer ${token}` },
        cache: "no-store",
      });
    } catch (err) {
      onError?.(err instanceof Error ? err : new Error(String(err)));
      return;
    }
    if (!res.ok || !res.body) {
      onError?.(new Error(`SSE connect failed: ${res.status}`));
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let currentEvent = "message";

    try {
      while (!cancelled) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (line.startsWith("event: ")) {
            currentEvent = line.slice(7).trim();
          } else if (line.startsWith("data: ")) {
            const raw = line.slice(6).trim();
            let parsed: unknown = raw;
            try {
              parsed = JSON.parse(raw);
            } catch {
              // keep as string
            }
            onEvent(currentEvent, parsed);
            if (currentEvent === "done") {
              onDone?.();
              return;
            }
            currentEvent = "message";
          }
        }
      }
    } finally {
      reader.cancel();
    }
    onDone?.();
  }

  connect().catch((err) => onError?.(err instanceof Error ? err : new Error(String(err))));

  return () => {
    cancelled = true;
  };
}
