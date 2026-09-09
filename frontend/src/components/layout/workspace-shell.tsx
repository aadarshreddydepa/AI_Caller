"use client";
import { Bell, Menu, Search, UserRound } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { useWorkspace } from "@/providers/workspace-provider";
import { useApi } from "@/hooks/use-api";
import { Sidebar } from "./sidebar";
import type { DashboardData } from "@/lib/types";

export function WorkspaceShell({ children }:{ children:React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const { session, businessId } = useWorkspace();
  const { data } = useApi<DashboardData>(`/backend/api/v1/businesses/${businessId}/dashboard/`);
  const business = session.memberships[0].business;
  return <div className="app-shell"><Sidebar open={open} close={() => setOpen(false)} session={session} newLeads={data?.leads.new || 0}/><main className="main-panel"><header className="topbar"><button className="menu-button" onClick={() => setOpen(true)} aria-label="Open navigation"><Menu size={21}/></button><div className="search-box"><Search size={17}/><span>Search calls, leads…</span><kbd>⌘ K</kbd></div><div className="top-actions"><Link className="icon-button" href="/notifications" aria-label="Notifications"><Bell size={19}/></Link><div className="live-pill"><span/>{business.status === "active" ? "Agent online" : business.status}</div><Link className="profile-button" href="/profile" aria-label="Open profile" title={session.user.email}><UserRound size={18}/></Link></div></header>{children}</main></div>;
}
