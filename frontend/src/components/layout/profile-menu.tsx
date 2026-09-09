"use client";
import { LogOut, Settings, UserRound } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { clearApiCache } from "@/hooks/use-api";
import { apiRequest } from "@/lib/api";
import { displayName, initials } from "@/lib/format";
import type { Session } from "@/lib/types";

export function ProfileMenu({ session }:{ session:Session }) {
  const router=useRouter();const[open,setOpen]=useState(false);const root=useRef<HTMLDivElement>(null);const name=displayName(session.user.name,session.user.email);const member=session.memberships[0];
  useEffect(()=>{function outside(event:MouseEvent){if(!root.current?.contains(event.target as Node))setOpen(false)}document.addEventListener("mousedown",outside);return()=>document.removeEventListener("mousedown",outside)},[]);
  async function signOut(){await apiRequest("/backend/api/v1/auth/logout/",{method:"POST"});clearApiCache();router.replace("/auth/login");router.refresh()}
  return <div className="profile-menu" ref={root}><button className="profile-button" onClick={()=>setOpen(value=>!value)} aria-label="Open account menu" aria-expanded={open}><span>{initials(name)}</span></button>{open&&<div className="profile-popover"><div className="profile-summary"><div className="avatar">{initials(name)}</div><div><strong>{name}</strong><span>{session.user.email}</span><small>{member.role} · {member.business.name}</small></div></div><div className="profile-links"><Link href="/dashboard/profile" onClick={()=>setOpen(false)}><UserRound size={16}/><span>Your profile</span></Link><Link href="/dashboard/settings" onClick={()=>setOpen(false)}><Settings size={16}/><span>Business settings</span></Link></div><button className="profile-signout" onClick={signOut}><LogOut size={16}/><span>Sign out</span></button></div>}</div>;
}
