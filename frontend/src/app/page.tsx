"use client";

import {
  Bell, BookOpenText, Building2, CalendarDays, ChevronDown, CircleHelp,
  Clock3, FileQuestion, LayoutDashboard, Mail, Menu, MessageSquareText, PhoneCall,
  Search, Settings, Sparkles, UserRound, UsersRound, X,
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
type PageKey = "overview" | "calls" | "leads" | "appointments" | "knowledge" | "notifications" | "settings" | "profile";
type Call = DashboardData["recent_calls"][number] & { status: string; duration_seconds: number; after_hours: boolean };
type Lead = { id: string; caller_name: string; caller_phone: string; requirement: string; preferred_callback_time: string; urgency: string; status: string; created_at: string };
type Appointment = { id: string; caller_name: string | null; service_name: string | null; requested_date: string | null; requested_time: string | null; notes: string; status: string; created_at: string };
type Knowledge = { services: { id:string; name:string; description:string; price_from:string|null; price_to:string|null; price_note:string; duration_minutes:number|null; active:boolean }[]; faqs: { id:string; question:string; answer:string; category:string; active:boolean }[] };
type Notifications = { endpoints: { id:string; channel:string; destination:string; label:string; enabled:boolean; verified_at:string|null }[]; deliveries: { id:string; channel:string; destination:string; status:string; attempt_count:number; queued_at:string; sent_at:string|null }[] };
type BusinessSettings = Business & { legal_name:string; description:string; timezone:string; default_language:string; phone:string; email:string; website:string; service_area:string; escalation_instructions:string };

const nav: { label:string; icon:typeof LayoutDashboard; key:PageKey }[] = [
  { label: "Overview", icon: LayoutDashboard, key:"overview" },
  { label: "Calls", icon: PhoneCall, key:"calls" },
  { label: "Leads", icon: UsersRound, key:"leads" },
  { label: "Appointments", icon: CalendarDays, key:"appointments" },
  { label: "Knowledge", icon: BookOpenText, key:"knowledge" },
  { label: "Notifications", icon: MessageSquareText, key:"notifications" },
];

function initials(name: string) {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase() || "U";
}

function Sidebar({ open, close, session, business, newLeads, page, navigate }: { open: boolean; close: () => void; session: Session; business: Business; newLeads: number; page:PageKey; navigate:(page:PageKey)=>void }) {
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
            <button className={`nav-item ${page === item.key ? "active" : ""}`} onClick={() => { navigate(item.key); close(); }} key={item.label}>
              <item.icon size={18} strokeWidth={1.8} /><span>{item.label}</span>
              {item.label === "Leads" && newLeads > 0 && <em>{newLeads}</em>}
            </button>
          ))}
          <p className="nav-label secondary">Manage</p>
          <button className={`nav-item ${page === "settings" ? "active" : ""}`} onClick={() => navigate("settings")}><Settings size={18} /><span>Business settings</span></button>
          <a className="nav-item" href="#"><CircleHelp size={18} /><span>Help & support</span></a>
        </nav>
        <button className="sidebar-footer" onClick={() => navigate("profile")}>
          <div className="avatar">{initials(displayName)}</div><div><strong>{displayName}</strong><span>{member.role}</span></div><ChevronDown size={15} />
        </button>
      </aside>
    </>
  );
}

function LoginScreen({ onLogin, googleEnabled }: { onLogin: () => void; googleEnabled: boolean }) {
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    const form = new FormData(event.currentTarget);
    const password = String(form.get("password") || "");
    const passwordConfirm = String(form.get("password_confirm") || "");
    if (mode === "signup" && password !== passwordConfirm) { setError("Passwords do not match."); setSubmitting(false); return; }
    if (mode === "signup" && password.length < 10) { setError("Use at least 10 characters for your password."); setSubmitting(false); return; }
    const payload = mode === "signup"
      ? { name: form.get("name"), business_name: form.get("business_name"), email: form.get("email"), password, password_confirm: passwordConfirm }
      : { email: form.get("email"), password };
    const response = await fetch(`/backend/api/v1/auth/${mode === "signup" ? "signup" : "login"}/`, {
      method: "POST", credentials: "include", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    setSubmitting(false);
    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      const first = Object.values(detail).flat().find(Boolean);
      setError(typeof first === "string" ? first : mode === "signup" ? "Please check the form and try again." : "That email and password did not match.");
      return;
    }
    onLogin();
  }

  return <main className="login-page">
    <section className="login-story">
      <div className="story-brand"><span><Sparkles size={19} /></span> AI Caller</div>
      <div className="story-copy"><p>CALL OPERATIONS</p><h1>Every call becomes<br />a clear next step.</h1><span>See what customers need, which leads require attention, and how your AI receptionist performs—without listening to every conversation.</span></div>
    </section>
    <section className="login-panel"><div className="login-card"><p className="eyebrow">BUSINESS PORTAL</p><h2>{mode === "signup" ? "Create your workspace" : "Welcome back"}</h2><span className="login-subtitle">{mode === "signup" ? "Start setting up your AI receptionist." : "Sign in to manage your AI receptionist."}</span>
      <form action="/backend/_allauth/browser/v1/auth/provider/redirect" method="post" className="google-form">
        <input type="hidden" name="provider" value="google" /><input type="hidden" name="process" value={mode === "signup" ? "signup" : "login"} /><input type="hidden" name="callback_url" value="http://localhost:3000" />
        <button type="submit" className="google-button" disabled={!googleEnabled}><b>G</b> {googleEnabled ? "Continue with Google" : "Google Sign-In not configured"}</button>
      </form>
      <div className="divider"><span>or continue with email</span></div>
      <form onSubmit={submit} className="login-form">
        {mode === "signup" && <div className="form-grid"><label>Your name<input name="name" autoComplete="name" minLength={2} maxLength={160} required /></label><label>Business name<input name="business_name" autoComplete="organization" minLength={2} maxLength={160} required /></label></div>}
        <label>Email address<input name="email" type="email" autoComplete="email" maxLength={254} required /></label>
        <label>Password<input name="password" type="password" autoComplete={mode === "signup" ? "new-password" : "current-password"} minLength={mode === "signup" ? 10 : undefined} maxLength={128} required /></label>
        {mode === "signup" && <label>Confirm password<input name="password_confirm" type="password" autoComplete="new-password" minLength={10} maxLength={128} required /></label>}
        {error && <p className="form-error">{error}</p>}<button className="signin-button" disabled={submitting}>{submitting ? "Please wait…" : mode === "signup" ? "Create account" : "Sign in"}</button>
      </form>
      <p className="auth-toggle">{mode === "signup" ? "Already have an account?" : "New to AI Caller?"} <button onClick={() => { setMode(mode === "signup" ? "signin" : "signup"); setError(""); }}>{mode === "signup" ? "Sign in" : "Create account"}</button></p>
    </div></section>
  </main>;
}

function Dashboard({ session, data, navigate }: { session: Session; data: DashboardData; navigate:(page:PageKey)=>void }) {
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
      <Sidebar open={menuOpen} close={() => setMenuOpen(false)} session={session} business={data.business} newLeads={data.leads.new} page="overview" navigate={navigate} />
      <main className="main-panel">
        <header className="topbar">
          <button className="menu-button" onClick={() => setMenuOpen(true)} aria-label="Open navigation"><Menu size={21} /></button>
          <div className="search-box"><Search size={17} /><span>Search calls, leads…</span><kbd>⌘ K</kbd></div>
          <div className="top-actions">
            <button className="icon-button" aria-label="Notifications"><Bell size={19} /></button>
            <button className="live-pill"><span /> {data.business.status === "active" ? "Agent online" : data.business.status}</button>
            <button className="profile-button" onClick={() => navigate("profile")} aria-label="Open profile" title={session.user.email}><UserRound size={18} /></button>
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
            <div className="panel-heading"><div><h2>Recent calls</h2><p>Latest conversations handled by your agent</p></div><button className="text-button" onClick={() => navigate("calls")}>View all calls →</button></div>
            <div className="table-scroll"><table><thead><tr><th>Caller</th><th>Requirement</th><th>Time</th><th>Outcome</th><th><span className="sr-only">Open</span></th></tr></thead><tbody>
              {recentCalls.map((call) => <tr key={`${call.phone}-${call.time}`}><td><div className="caller-cell"><span>{call.name.charAt(0)}</span><div><strong>{call.name}</strong><small>{call.phone}</small></div></div></td><td>{call.need}</td><td>{call.time}</td><td><mark className={`status ${call.tone}`}>{call.status}</mark></td><td><button className="row-action">View</button></td></tr>)}
            </tbody></table></div>
          </section>
        </div>
      </main>
    </div>
  );
}

const pageCopy: Record<Exclude<PageKey, "overview">, { title:string; subtitle:string }> = {
  calls: { title:"Calls", subtitle:"Review every conversation handled by your receptionist." },
  leads: { title:"Leads", subtitle:"Follow up with callers who asked for help or a callback." },
  appointments: { title:"Appointments", subtitle:"Track booking, rescheduling, and confirmation requests." },
  knowledge: { title:"Knowledge", subtitle:"The live services and answers your receptionist can use." },
  notifications: { title:"Notifications", subtitle:"See where owner summaries go and whether they were delivered." },
  settings: { title:"Business settings", subtitle:"Keep the information your receptionist shares accurate." },
  profile: { title:"Your profile", subtitle:"Manage the identity associated with this workspace." },
};

function csrfToken() {
  return document.cookie.split("; ").find((row) => row.startsWith("csrftoken="))?.split("=")[1] || "";
}

function EmptyState({ children }: { children:string }) { return <div className="empty-state"><Sparkles size={22} /><strong>Nothing here yet</strong><span>{children}</span></div>; }

function WorkspacePage({ page, session, business, newLeads, data, navigate, refresh, onSignedOut }: { page:Exclude<PageKey,"overview">; session:Session; business:Business; newLeads:number; data:unknown; navigate:(page:PageKey)=>void; refresh:()=>void; onSignedOut:()=>void }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [notice, setNotice] = useState("");
  const calls = (data || []) as Call[];
  const leads = (data || []) as Lead[];
  const appointments = (data || []) as Appointment[];
  const knowledge = (data || { services:[], faqs:[] }) as Knowledge;
  const notifications = (data || { endpoints:[], deliveries:[] }) as Notifications;
  const settings = (data || {}) as BusinessSettings;
  const profile = (data || {}) as { id:string; email:string; name:string; phone:string };

  async function save(event:FormEvent<HTMLFormElement>, endpoint:string) {
    event.preventDefault(); setNotice("Saving…");
    const values = Object.fromEntries(new FormData(event.currentTarget).entries());
    const response = await fetch(endpoint, { method:"PATCH", credentials:"include", headers:{ "Content-Type":"application/json", "X-CSRFToken":csrfToken() }, body:JSON.stringify(values) });
    if (!response.ok) { const body = await response.json().catch(() => ({})); setNotice(Object.values(body).flat().join(" ") || "Could not save changes."); return; }
    setNotice("Changes saved."); refresh();
  }
  async function signOut() {
    await fetch("/backend/api/v1/auth/logout/", { method:"POST", credentials:"include", headers:{ "X-CSRFToken":csrfToken() } });
    onSignedOut();
  }

  return <div className="app-shell">
    <Sidebar open={menuOpen} close={() => setMenuOpen(false)} session={session} business={business} newLeads={newLeads} page={page} navigate={navigate} />
    <main className="main-panel">
      <header className="topbar"><button className="menu-button" onClick={() => setMenuOpen(true)} aria-label="Open navigation"><Menu size={21} /></button><div className="search-box"><Search size={17} /><span>Search this workspace…</span><kbd>⌘ K</kbd></div><div className="top-actions"><button className="icon-button" onClick={() => navigate("notifications")} aria-label="Notifications"><Bell size={19} /></button><button className="live-pill"><span /> {business.status}</button><button className="profile-button" onClick={() => navigate("profile")} aria-label="Open profile"><UserRound size={18} /></button></div></header>
      <div className="content"><section className="page-heading"><div><p>AI CALLER WORKSPACE</p><h1>{pageCopy[page].title}</h1><span>{pageCopy[page].subtitle}</span></div></section>

      {page === "calls" && <section className="panel data-panel">{calls.length === 0 ? <EmptyState>Your calls will appear as soon as the agent answers one.</EmptyState> : <div className="table-scroll"><table><thead><tr><th>Caller</th><th>Status</th><th>Started</th><th>Duration</th><th>Routing</th></tr></thead><tbody>{calls.map(call => <tr key={call.id}><td><div className="caller-cell"><span>{(call.caller_name || "U")[0]}</span><div><strong>{call.caller_name || "Unknown caller"}</strong><small>{call.caller_phone || "Number unavailable"}</small></div></div></td><td><mark className="status green">{call.status}</mark></td><td>{new Date(call.started_at).toLocaleString()}</td><td>{Math.floor(call.duration_seconds / 60)}m {call.duration_seconds % 60}s</td><td>{call.escalated ? "Escalated" : call.after_hours ? "After hours" : "AI handled"}</td></tr>)}</tbody></table></div>}</section>}

      {page === "leads" && <section className="panel data-panel">{leads.length === 0 ? <EmptyState>Captured caller requirements will appear here.</EmptyState> : <div className="table-scroll"><table><thead><tr><th>Contact</th><th>Requirement</th><th>Callback</th><th>Urgency</th><th>Status</th></tr></thead><tbody>{leads.map(lead => <tr key={lead.id}><td><div className="caller-cell"><span>{(lead.caller_name || "U")[0]}</span><div><strong>{lead.caller_name || "Unknown caller"}</strong><small>{lead.caller_phone || "No phone supplied"}</small></div></div></td><td>{lead.requirement || "General enquiry"}</td><td>{lead.preferred_callback_time || "Not specified"}</td><td>{lead.urgency}</td><td><mark className={`status ${lead.status === "new" ? "amber" : "green"}`}>{lead.status}</mark></td></tr>)}</tbody></table></div>}</section>}

      {page === "appointments" && <section className="card-grid">{appointments.length === 0 ? <div className="panel full-span"><EmptyState>Booking and rescheduling requests will appear here.</EmptyState></div> : appointments.map(item => <article className="panel item-card" key={item.id}><div className="item-icon"><CalendarDays size={19} /></div><div><span className="status amber">{item.status.replaceAll("_"," ")}</span><h2>{item.caller_name || "Unknown caller"}</h2><p>{item.service_name || item.notes || "General appointment request"}</p><small><Clock3 size={14} /> {item.requested_date || "Date pending"} {item.requested_time?.slice(0,5) || ""}</small></div></article>)}</section>}

      {page === "knowledge" && <><section className="section-title"><div><h2>Services</h2><p>{knowledge.services.length} live service records</p></div></section><section className="card-grid">{knowledge.services.length === 0 ? <div className="panel full-span"><EmptyState>Add services through the API to teach the receptionist.</EmptyState></div> : knowledge.services.map(item => <article className="panel item-card" key={item.id}><div className="item-icon"><Sparkles size={19} /></div><div><span className={`status ${item.active ? "green" : "rose"}`}>{item.active ? "active" : "inactive"}</span><h2>{item.name}</h2><p>{item.description}</p><small>{item.price_note || (item.price_from ? `From ₹${item.price_from}` : "Ask business for price")}{item.duration_minutes ? ` · ${item.duration_minutes} min` : ""}</small></div></article>)}</section><section className="section-title spaced"><div><h2>Frequently asked questions</h2><p>{knowledge.faqs.length} approved answers</p></div></section><section className="faq-list">{knowledge.faqs.map(item => <article className="panel faq-card" key={item.id}><FileQuestion size={18} /><div><h3>{item.question}</h3><p>{item.answer}</p><small>{item.category || "General"}</small></div></article>)}</section></>}

      {page === "notifications" && <><section className="card-grid">{notifications.endpoints.map(item => <article className="panel item-card" key={item.id}><div className="item-icon"><Mail size={19} /></div><div><span className={`status ${item.enabled ? "green" : "rose"}`}>{item.enabled ? "enabled" : "disabled"}</span><h2>{item.label || item.channel}</h2><p>{item.destination}</p><small>{item.verified_at ? "Verified destination" : "Verification pending"}</small></div></article>)}{notifications.endpoints.length === 0 && <div className="panel full-span"><EmptyState>No owner notification destination is configured.</EmptyState></div>}</section><section className="panel data-panel spaced">{notifications.deliveries.length === 0 ? <EmptyState>Delivery history will appear after a call summary is sent.</EmptyState> : <div className="table-scroll"><table><thead><tr><th>Channel</th><th>Destination</th><th>Status</th><th>Attempts</th><th>Queued</th></tr></thead><tbody>{notifications.deliveries.map(item => <tr key={item.id}><td>{item.channel}</td><td>{item.destination}</td><td><mark className={`status ${item.status === "sent" || item.status === "delivered" ? "green" : item.status === "failed" ? "rose" : "amber"}`}>{item.status}</mark></td><td>{item.attempt_count}</td><td>{new Date(item.queued_at).toLocaleString()}</td></tr>)}</tbody></table></div>}</section></>}

      {page === "settings" && settings.id && <form className="panel settings-form" onSubmit={(event) => save(event, `/backend/api/v1/businesses/${business.id}/settings/`)}><div className="form-section"><h2>Business identity</h2><p>This is the source of truth used during calls.</p><div className="settings-grid"><label>Business name<input name="name" defaultValue={settings.name} required maxLength={160} /></label><label>Legal name<input name="legal_name" defaultValue={settings.legal_name} maxLength={200} /></label><label>Email<input name="email" type="email" defaultValue={settings.email} /></label><label>Phone<input name="phone" type="tel" defaultValue={settings.phone} maxLength={32} /></label><label>Website<input name="website" type="url" defaultValue={settings.website} /></label><label>Service area<input name="service_area" defaultValue={settings.service_area} maxLength={255} /></label></div><label>Description<textarea name="description" defaultValue={settings.description} rows={4} required /></label><label>Escalation instructions<textarea name="escalation_instructions" defaultValue={settings.escalation_instructions} rows={4} /></label></div><div className="form-actions"><span>{notice}</span><button className="primary-button">Save changes</button></div></form>}

      {page === "profile" && profile.id && <div className="profile-layout"><form className="panel settings-form" onSubmit={(event) => save(event, "/backend/api/v1/auth/profile/")}><div className="profile-hero"><div className="large-avatar">{initials(profile.name || profile.email)}</div><div><h2>{profile.name || "Workspace user"}</h2><p>{profile.email}</p></div></div><div className="settings-grid"><label>Full name<input name="name" defaultValue={profile.name} maxLength={160} required /></label><label>Phone<input name="phone" type="tel" defaultValue={profile.phone} maxLength={32} /></label></div><div className="form-actions"><span>{notice}</span><button className="primary-button">Save profile</button></div></form><aside className="panel account-card"><h2>Account access</h2><p>Signed in as <strong>{profile.email}</strong>. Your permissions are controlled by your workspace role.</p><button className="danger-button" onClick={signOut}>Sign out</button></aside></div>}
      </div>
    </main>
  </div>;
}

export default function Home() {
  const [session, setSession] = useState<Session | null>(null);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [page, setPage] = useState<PageKey>("overview");
  const [pageData, setPageData] = useState<unknown>(null);
  const [pageLoading, setPageLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [googleEnabled, setGoogleEnabled] = useState(false);

  async function loadSession() {
    setLoading(true);
    const response = await fetch("/backend/api/v1/auth/session/", { credentials: "include" });
    const nextSession = await response.json();
    setGoogleEnabled(Boolean(nextSession.google_enabled));
    setSession(nextSession.authenticated ? nextSession : null);
    if (!nextSession.authenticated) { setDashboard(null); setPageData(null); setPage("overview"); }
    setLoading(false);
  }

  async function loadPage(target:PageKey = page) {
    const businessId = session?.memberships[0]?.business.id;
    if (!businessId || target === "overview") return;
    setPageLoading(true);
    const endpoint = target === "profile" ? "/backend/api/v1/auth/profile/" : `/backend/api/v1/businesses/${businessId}/${target}/`;
    const response = await fetch(endpoint, { credentials:"include" });
    setPageData(response.ok ? await response.json() : null);
    setPageLoading(false);
  }
  function navigateTo(target:PageKey) {
    if (target !== page) setPageData(null);
    setPage(target);
    if (target !== "overview") void loadPage(target);
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
  if (page === "overview") return <Dashboard session={session} data={dashboard} navigate={navigateTo} />;
  if (pageLoading || pageData === null) return <div className="app-loading"><span><Sparkles size={20} /></span><p>Loading {page}…</p></div>;
  return <WorkspacePage page={page} session={session} business={dashboard.business} newLeads={dashboard.leads.new} data={pageData} navigate={navigateTo} refresh={() => void loadPage(page)} onSignedOut={() => void loadSession()} />;
}
