"use client";
import { FormEvent, useEffect, useState } from "react";
import { Sparkles } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiRequest } from "@/lib/api";
import type { Session } from "@/lib/types";

export function AuthForm({ mode }:{ mode:"login"|"signup" }) {
  const router = useRouter();
  const [googleEnabled, setGoogleEnabled] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  useEffect(() => { apiRequest<Session>("/backend/api/v1/auth/session/").then(session => { setGoogleEnabled(session.google_enabled); if (session.authenticated) router.replace("/overview"); }).catch(() => undefined); }, [router]);
  async function submit(event:FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setSubmitting(true);
    const form = new FormData(event.currentTarget); const password = String(form.get("password") || ""); const confirmation = String(form.get("password_confirm") || "");
    if (mode === "signup" && password !== confirmation) { setError("Passwords do not match."); setSubmitting(false); return; }
    try {
      await apiRequest(`/backend/api/v1/auth/${mode}/`, { method:"POST", body:JSON.stringify(mode === "signup" ? { name:form.get("name"), business_name:form.get("business_name"), email:form.get("email"), password, password_confirm:confirmation } : { email:form.get("email"), password }) });
      router.replace("/overview"); router.refresh();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Please check the form and try again."); }
    finally { setSubmitting(false); }
  }
  const signup = mode === "signup";
  return <main className="login-page"><section className="login-story"><div className="story-brand"><span><Sparkles size={19}/></span>AI Caller</div><div className="story-copy"><p>CALL OPERATIONS</p><h1>Every call becomes<br/>a clear next step.</h1><span>Understand what customers need, capture qualified leads, and keep business owners informed automatically.</span></div></section><section className="login-panel"><div className="login-card"><p className="eyebrow">BUSINESS PORTAL</p><h2>{signup ? "Create your workspace" : "Welcome back"}</h2><span className="login-subtitle">{signup ? "Start setting up your AI receptionist." : "Sign in to manage your AI receptionist."}</span><form action="/backend/_allauth/browser/v1/auth/provider/redirect" method="post" className="google-form"><input type="hidden" name="provider" value="google"/><input type="hidden" name="process" value={signup ? "signup" : "login"}/><input type="hidden" name="callback_url" value="http://localhost:3000/overview"/><button type="submit" className="google-button" disabled={!googleEnabled}><b>G</b>{googleEnabled ? "Continue with Google" : "Google Sign-In not configured"}</button></form><div className="divider"><span>or continue with email</span></div><form onSubmit={submit} className="login-form">{signup && <div className="form-grid"><label>Your name<input name="name" autoComplete="name" minLength={2} maxLength={160} required/></label><label>Business name<input name="business_name" autoComplete="organization" minLength={2} maxLength={160} required/></label></div>}<label>Email address<input name="email" type="email" autoComplete="email" maxLength={254} required/></label><label>Password<input name="password" type="password" autoComplete={signup ? "new-password" : "current-password"} minLength={signup ? 10 : undefined} maxLength={128} required/></label>{signup && <label>Confirm password<input name="password_confirm" type="password" autoComplete="new-password" minLength={10} maxLength={128} required/></label>}{error && <p className="form-error">{error}</p>}<button className="signin-button" disabled={submitting}>{submitting ? "Please wait…" : signup ? "Create account" : "Sign in"}</button></form><p className="auth-toggle">{signup ? "Already have an account?" : "New to AI Caller?"} <Link href={signup ? "/login" : "/signup"}>{signup ? "Sign in" : "Create account"}</Link></p></div></section></main>;
}
