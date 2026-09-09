"use client";
import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";

const cache = new Map<string, unknown>();

export function clearApiCache(prefix?:string) {
  if (!prefix) cache.clear();
  else for (const key of cache.keys()) if (key.startsWith(prefix)) cache.delete(key);
}

export function useApi<T>(url:string|null) {
  const [data, setData] = useState<T|undefined>(() => url ? cache.get(url) as T|undefined : undefined);
  const [error, setError] = useState("");
  useEffect(() => {
    if (!url) return;
    const cached = cache.get(url) as T|undefined;
    if (cached !== undefined) { queueMicrotask(() => setData(cached)); return; }
    const controller = new AbortController();
    apiRequest<T>(url, { signal:controller.signal }).then((result) => { cache.set(url, result); setData(result); setError(""); }).catch((reason) => { if (reason.name !== "AbortError") setError(reason.message); });
    return () => controller.abort();
  }, [url]);
  async function refresh() {
    if (!url) return;
    cache.delete(url);
    const result = await apiRequest<T>(url);
    cache.set(url, result); setData(result);
  }
  return { data, error, loading:data === undefined && !error, refresh };
}
