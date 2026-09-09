export function csrfToken() {
  if (typeof document === "undefined") return "";
  return document.cookie.split("; ").find((row) => row.startsWith("csrftoken="))?.split("=")[1] || "";
}

export async function apiRequest<T>(url:string, init:RequestInit = {}):Promise<T> {
  const response = await fetch(url, { credentials:"include", ...init, headers:{ ...(init.body ? { "Content-Type":"application/json" } : {}), ...(init.method && init.method !== "GET" ? { "X-CSRFToken":csrfToken() } : {}), ...init.headers } });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const message = Object.values(body).flat().find(Boolean);
    throw new Error(typeof message === "string" ? message : "The request could not be completed.");
  }
  return response.status === 204 ? undefined as T : response.json();
}
