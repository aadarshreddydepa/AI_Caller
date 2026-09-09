"use client";

import {
  Bell, BookOpenText, Building2, CalendarDays, ChevronDown, CircleHelp,
  LayoutDashboard, Menu, MessageSquareText, PhoneCall, Search, Settings,
  Sparkles, UserRound, UsersRound, X,
} from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import {
  Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from "recharts";

type Business = { id: string; name: string; slug: string; status: string };
type Session = { authenticated: boolean; user: { id: string; email: string; name: string }; memberships: { id: string; role: string; business: Business }[] };
type DashboardData = {
  business: Business;
  calls: { total: number; completed: number; escalated: number; after_hours: number };
  leads: { total: number; new: number; converted: number };
  activity: { date: string; count: number }[];
  recent_calls: { id: string; caller_name: string; caller_phone: string; started_at: string; escalated: boolean; lead_id: string | null; lead_requirement: string | null }[];
};

const nav = [
  { label: "Overview", icon: LayoutDashboard, active: true },
  { label: "Calls", icon: PhoneCall },
  { label: "Leads", icon: UsersRound },
  { label: "Appointments", icon: CalendarDays },
  { label: "Knowledge", icon: BookOpenText },
  { label: "Notifications", icon: MessageSquareText },
];

function initials(name: string) {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase() || "U";
}

function Sidebar({ open, close, session, business, newLeads }: { open: boolean; close: () => void; session: Session; business: Business; newLeads: number }) {
  const member = session.memberships.find((item) => item.business.id === business.id)!;
  const displayName = session.user.name || session.user.email.split("@")[0];
  return (
    <>
      {open && <button className="sidebar-backdrop" aria-label="Close navigation" onClick={close} />}
      <aside className={`sidebar ${open ? "sidebar-open" : ""}`}>
        <div className="brand-row">
          <div className="brand-mark"><Sparkles size={18} /></div>
          <div><strong>AI Caller</strong><span>Business voice desk</span></div>
          <button className="mobile-close" onClick={close} aria-label="Close navigation"><X size={19} /></button>
        </div>
        <button className="workspace-switcher">
          <span className="workspace-icon"><Building2 size={17} /></span>
          <span><strong>{business.name}</strong><small>{business.status}</small></span>
          <ChevronDown size={15} />
        </button>
        <nav aria-label="Primary navigation">
          <p className="nav-label">Workspace</p>
          {nav.map((item) => (
            <a className={`nav-item ${item.active ? "active" : ""}`} href="#" key={item.label}>
              <item.icon size={18} strokeWidth={1.8} /><span>{item.label}</span>
              {item.label === "Leads" && newLeads > 0 && <em>{newLeads}</em>}
            </a>
          ))}
          <p className="nav-label secondary">Manage</p>
          <a className="nav-item" href="#"><Settings size={18} /><span>Business settings</span></a>
          <a className="nav-item" href="#"><CircleHelp size={18} /><span>Help & support</span></a>
        </nav>
        <div className="sidebar-footer">
          <div className="avatar">{initials(displayName)}</div><div><strong>{displayName}</strong><span>{member.role}</span></div><ChevronDown size={15} />
        </div>
      </aside>
    </>
  );
}

function LoginScreen({ onLogin, googleEnabled }: { onLogin: () => void; googleEnabled: boolean }) {
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    const form = new FormData(event.currentTarget);
    const response = await fetch("/backend/api/v1/auth/login/", {
      method: "POST", credentials: "include", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: form.get("email"), password: form.get("password") }),
    });
    setSubmitting(false);
    if (!response.ok) { setError("That email and password did not match."); return; }
    onLogin();
  }

  return <main className="login-page">
    <section className="login-story">
      <div className="story-brand"><span><Sparkles size={19} /></span> AI Caller</div>
      <div className="story-copy"><p>CALL OPERATIONS</p><h1>Every call becomes<br />a clear next step.</h1><span>See what customers need, which leads require attention, and how your AI receptionist performs—without listening to every conversation.</span></div>
    </section>
    <section className="login-panel"><div className="login-card"><p className="eyebrow">BUSINESS PORTAL</p><h2>Welcome back</h2><span className="login-subtitle">Sign in to manage your AI receptionist.</span>
      <form action="/backend/_allauth/browser/v1/auth/provider/redirect" method="post" className="google-form">
        <input type="hidden" name="provider" value="google" /><input type="hidden" name="process" value="login" /><input type="hidden" name="callback_url" value="http://localhost:3000" />
        <button type="submit" className="google-button" disabled={!googleEnabled}><b>G</b> {googleEnabled ? "Continue with Google" : "Google Sign-In not configured"}</button>
      </form>
      <div className="divider"><span>or continue with email</span></div>
      <form onSubmit={submit} className="login-form"><label>Email address<input name="email" type="email" autoComplete="email" required /></label><label>Password<input name="password" type="password" autoComplete="current-password" required /></label>{error && <p className="form-error">{error}</p>}<button className="signin-button" disabled={submitting}>{submitting ? "Signing in…" : "Sign in"}</button></form>
    </div></section>
  </main>;
}

function Dashboard({ session, data }: { session: Session; data: DashboardData }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [referenceTime] = useState(() => Date.now());
  const displayName = session.user.name || session.user.email.split("@")[0];
  const callbackCount = Math.max(data.leads.total - data.calls.escalated, 0);
  const resolved = Math.max(data.calls.total - callbackCount - data.calls.escalated, 0);
  const resolvedRate = data.calls.total ? Math.round((resolved / data.calls.total) * 100) : 0;
  const maxActivity = Math.max(...data.activity.map((item) => item.count), 1);
  const activityData = data.activity.map((item) => ({ day: new Intl.DateTimeFormat("en", { weekday:"short" }).format(new Date(`${item.date}T12:00:00`)), calls: item.count }));
  const outcomeData = [
    { name: "Resolved", value: resolved, color: "#6059ef" },
    { name: "Callback", value: callbackCount, color: "#f5b650" },
    { name: "Escalated", value: data.calls.escalated, color: "#f2747c" },
  ].filter((item) => item.value > 0);
  const recentCalls = data.recent_calls.map((call) => ({
    name: call.caller_name || "Unknown caller",
    phone: call.caller_phone ? `${call.caller_phone.slice(0, 5)}•••${call.caller_phone.slice(-4)}` : "Number unavailable",
    need: call.lead_requirement || "General enquiry",
    time: new Intl.RelativeTimeFormat("en", { numeric: "auto" }).format(-Math.max(0, Math.round((referenceTime - new Date(call.started_at).getTime()) / 3600000)), "hour"),
    status: call.escalated ? "Escalated" : call.lead_id ? "Callback" : "Resolved",
    tone: call.escalated ? "rose" : call.lead_id ? "amber" : "green",
  }));
  useEffect(() => {
    const context = document.modelContext;
    if (!context?.registerTool) return;
    const lifecycle = new AbortController();
    void Promise.resolve(context.registerTool({
      name: "read_call_dashboard_summary",
      title: "Read call dashboard summary",
      description: "Read the authenticated business's visible call, lead, and seven-day activity summary.",
      inputSchema: { type: "object", properties: {}, additionalProperties: false },
      annotations: { readOnlyHint: true, untrustedContentHint: false },
      execute: async () => ({ business: data.business.name, calls: data.calls, leads: data.leads, activity: data.activity }),
    }, { signal: lifecycle.signal })).catch(() => undefined);
    return () => lifecycle.abort();
  }, [data]);
  return (
    <div className="app-shell">
      <Sidebar open={menuOpen} close={() => setMenuOpen(false)} session={session} business={data.business} newLeads={data.leads.new} />
      <main className="main-panel">
        <header className="topbar">
          <button className="menu-button" onClick={() => setMenuOpen(true)} aria-label="Open navigation"><Menu size={21} /></button>
          <div className="search-box"><Search size={17} /><span>Search calls, leads…</span><kbd>⌘ K</kbd></div>
          <div className="top-actions">
            <button className="icon-button" aria-label="Notifications"><Bell size={19} /></button>
            <button className="live-pill"><span /> {data.business.status === "active" ? "Agent online" : data.business.status}</button>
            <button className="profile-button" aria-label="Open profile" title={session.user.email}><UserRound size={18} /></button>
          </div>
        </header>
        <div className="content">
          <section className="page-heading">
            <div><p>{new Intl.DateTimeFormat("en-IN", { weekday:"long", day:"numeric", month:"long" }).format(new Date())}</p><h1>Good evening, {displayName}</h1><span>Here’s how your AI receptionist is performing today.</span></div>
            <button className="primary-button"><PhoneCall size={17} /> Test your agent</button>
          </section>
          <section className="metric-grid" aria-label="Call metrics">
            <article className="metric-card"><div className="metric-label"><span>Total calls</span><PhoneCall size={17} /></div><strong>{data.calls.total}</strong><p><b>{data.calls.completed}</b> completed</p></article>
            <article className="metric-card"><div className="metric-label"><span>Leads captured</span><UsersRound size={17} /></div><strong>{data.leads.total}</strong><p><b>{data.leads.new}</b> need attention</p></article>
            <article className="metric-card"><div className="metric-label"><span>Resolved by AI</span><Sparkles size={17} /></div><strong>{resolvedRate}%</strong><p><b>{resolved}</b> without callback</p></article>
            <article className="metric-card"><div className="metric-label"><span>After-hours</span><CalendarDays size={17} /></div><strong>{data.calls.after_hours}</strong><p><b>Calls answered</b> while closed</p></article>
          </section>
          <section className="insight-grid">
            <article className="panel performance-panel">
              <div className="panel-heading"><div><h2>Call activity</h2><p>Answered calls over the last 7 days</p></div><button>This week <ChevronDown size={14} /></button></div>
              <div className="chart-wrap"><ResponsiveContainer width="100%" height="100%"><BarChart data={activityData} margin={{ top: 12, right: 8, left: -25, bottom: 0 }}><CartesianGrid stroke="#edf0f4" vertical={false} /><XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: "#8e96a3", fontSize: 11 }} /><YAxis allowDecimals={false} domain={[0, maxActivity]} axisLine={false} tickLine={false} tick={{ fill: "#a2a8b2", fontSize: 10 }} /><Tooltip cursor={{ fill: "#f4f3ff" }} contentStyle={{ border: "1px solid #e4e6ed", borderRadius: 10, boxShadow: "0 10px 30px #14213d14", fontSize: 12 }} /><Bar dataKey="calls" fill="#6b63f6" radius={[6, 6, 2, 2]} maxBarSize={36} /></BarChart></ResponsiveContainer></div>
            </article>
            <article className="panel outcomes-panel">
              <div className="panel-heading"><div><h2>Call outcomes</h2><p>Where conversations ended</p></div></div>
              <div className="outcome-visual"><div className="pie-wrap"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={outcomeData} dataKey="value" nameKey="name" innerRadius={43} outerRadius={62} paddingAngle={3} stroke="none">{outcomeData.map((item) => <Cell key={item.name} fill={item.color} />)}</Pie><Tooltip contentStyle={{ border:"1px solid #e4e6ed", borderRadius:10, fontSize:12 }} /></PieChart></ResponsiveContainer><span><strong>{data.calls.total}</strong><small>total</small></span></div></div>
              <div className="legend"><span><i className="indigo" />Resolved <b>{resolved}</b></span><span><i className="amber" />Callback <b>{callbackCount}</b></span><span><i className="rose" />Escalated <b>{data.calls.escalated}</b></span></div>
            </article>
          </section>
          <section className="panel recent-panel">
            <div className="panel-heading"><div><h2>Recent calls</h2><p>Latest conversations handled by your agent</p></div><a href="#">View all calls →</a></div>
            <div className="table-scroll"><table><thead><tr><th>Caller</th><th>Requirement</th><th>Time</th><th>Outcome</th><th><span className="sr-only">Open</span></th></tr></thead><tbody>
              {recentCalls.map((call) => <tr key={`${call.phone}-${call.time}`}><td><div className="caller-cell"><span>{call.name.charAt(0)}</span><div><strong>{call.name}</strong><small>{call.phone}</small></div></div></td><td>{call.need}</td><td>{call.time}</td><td><mark className={`status ${call.tone}`}>{call.status}</mark></td><td><button className="row-action">View</button></td></tr>)}
            </tbody></table></div>
          </section>
        </div>
      </main>
    </div>
  );
}

export default function Home() {
  const [session, setSession] = useState<Session | null>(null);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [googleEnabled, setGoogleEnabled] = useState(false);

  async function loadSession() {
    setLoading(true);
    const response = await fetch("/backend/api/v1/auth/session/", { credentials: "include" });
    const nextSession = await response.json();
    setGoogleEnabled(Boolean(nextSession.google_enabled));
    setSession(nextSession.authenticated ? nextSession : null);
    setLoading(false);
  }

  useEffect(() => {
    let active = true;
    void fetch("/backend/api/v1/auth/session/", { credentials: "include" })
      .then((response) => response.json())
      .then((nextSession) => {
        if (!active) return;
        setGoogleEnabled(Boolean(nextSession.google_enabled));
        setSession(nextSession.authenticated ? nextSession : null);
        setLoading(false);
      });
    return () => { active = false; };
  }, []);
  useEffect(() => {
    const businessId = session?.memberships[0]?.business.id;
    if (!businessId) return;
    void fetch(`/backend/api/v1/businesses/${businessId}/dashboard/`, { credentials: "include" })
      .then((response) => response.ok ? response.json() : Promise.reject())
      .then(setDashboard);
  }, [session]);

  if (loading) return <div className="app-loading"><span><Sparkles size={20} /></span><p>Preparing your call desk…</p></div>;
  if (!session) return <LoginScreen onLogin={loadSession} googleEnabled={googleEnabled} />;
  if (!dashboard) return <div className="app-loading"><span><Sparkles size={20} /></span><p>Loading business activity…</p></div>;
  return <Dashboard session={session} data={dashboard} />;
}
