"use client";
import { BookOpenText, Building2, CalendarDays, ChevronDown, CircleHelp, LayoutDashboard, MessageSquareText, PhoneCall, Settings, Sparkles, UsersRound, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { displayName, initials } from "@/lib/format";
import type { Session } from "@/lib/types";

const navigation = [
  { label:"Overview", href:"/dashboard/overview", icon:LayoutDashboard }, { label:"Calls", href:"/dashboard/calls", icon:PhoneCall },
  { label:"Leads", href:"/dashboard/leads", icon:UsersRound }, { label:"Appointments", href:"/dashboard/appointments", icon:CalendarDays },
  { label:"Knowledge", href:"/dashboard/knowledge", icon:BookOpenText }, { label:"Notifications", href:"/dashboard/notifications", icon:MessageSquareText },
];

export function Sidebar({ open, close, session, newLeads }:{ open:boolean; close:()=>void; session:Session; newLeads:number }) {
  const pathname = usePathname();
  const member = session.memberships[0];
  const name = displayName(session.user.name, session.user.email);
  return <>
    {open && <button className="sidebar-backdrop" aria-label="Close navigation" onClick={close} />}
    <aside className={`sidebar ${open ? "sidebar-open" : ""}`}>
      <div className="brand-row"><div className="brand-mark"><Sparkles size={18}/></div><div><strong>AI Caller</strong><span>Business voice desk</span></div><button className="mobile-close" onClick={close} aria-label="Close navigation"><X size={19}/></button></div>
      <div className="workspace-switcher"><span className="workspace-icon"><Building2 size={17}/></span><span><strong>{member.business.name}</strong><small>{member.business.status}</small></span><ChevronDown size={15}/></div>
      <nav aria-label="Primary navigation"><p className="nav-label">Workspace</p>{navigation.map(item => <Link className={`nav-item ${pathname === item.href ? "active" : ""}`} href={item.href} onClick={close} key={item.href}><item.icon size={18} strokeWidth={1.8}/><span>{item.label}</span>{item.href === "/dashboard/leads" && newLeads > 0 && <em>{newLeads}</em>}</Link>)}<p className="nav-label secondary">Manage</p><Link className={`nav-item ${pathname === "/dashboard/settings" ? "active" : ""}`} href="/dashboard/settings"><Settings size={18}/><span>Business settings</span></Link><span className="nav-item muted"><CircleHelp size={18}/><span>Help & support</span></span></nav>
      <Link className="sidebar-footer" href="/dashboard/profile"><div className="avatar">{initials(name)}</div><div><strong>{name}</strong><span>{member.role}</span></div><ChevronDown size={15}/></Link>
    </aside>
  </>;
}
