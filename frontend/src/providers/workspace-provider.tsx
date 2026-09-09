"use client";
import { createContext, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiGet } from "@/lib/api";
import type { Session } from "@/lib/types";

type WorkspaceContextValue = { session:Session; businessId:string; refreshSession:()=>Promise<void> };
const WorkspaceContext = createContext<WorkspaceContextValue|null>(null);

export function WorkspaceProvider({ children }:{ children:React.ReactNode }) {
  const router = useRouter();
  const [session, setSession] = useState<Session|null>(null);
  const [ready, setReady] = useState(false);
  async function refreshSession() {
    const next = await apiGet<Session>("/backend/api/v1/auth/session/");
    if (!next.authenticated || !next.memberships?.length) { router.replace("/auth/login"); setReady(true); return; }
    setSession(next); setReady(true);
  }
  useEffect(() => {
    let active = true;
    void apiGet<Session>("/backend/api/v1/auth/session/").then((next) => {
      if (!active) return;
      if (!next.authenticated || !next.memberships?.length) { router.replace("/auth/login"); setReady(true); return; }
      setSession(next); setReady(true);
    });
    return () => { active = false; };
  }, [router]);
  if (!ready || !session) return <div className="app-loading"><span>AI</span><p>Preparing your workspace…</p></div>;
  return <WorkspaceContext.Provider value={{ session, businessId:session.memberships[0].business.id, refreshSession }}>{children}</WorkspaceContext.Provider>;
}

export function useWorkspace() {
  const value = useContext(WorkspaceContext);
  if (!value) throw new Error("useWorkspace must be used inside WorkspaceProvider");
  return value;
}
