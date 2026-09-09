"use client";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

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
    let active = true;
    void apiGet<T>(url).then((result) => {
      cache.set(url, result);
      if (active) { setData(result); setError(""); }
    }).catch((reason) => { if (active) setError(reason.message); });
    return () => { active = false; };
  }, [url]);
  async function refresh() {
    if (!url) return;
    cache.delete(url);
    const result = await apiGet<T>(url);
    cache.set(url, result); setData(result);
  }
  return { data, error, loading:data === undefined && !error, refresh };
}
