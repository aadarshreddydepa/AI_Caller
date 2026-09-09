import { Sparkles } from "lucide-react";
export function PageLoading() { return <div className="content"><div className="content-skeleton"><span/><span/><span/></div></div>; }
export function EmptyState({ children }:{ children:string }) { return <div className="empty-state"><Sparkles size={22}/><strong>Nothing here yet</strong><span>{children}</span></div>; }
export function PageError({ message }:{ message:string }) { return <div className="content"><div className="panel empty-state"><strong>Unable to load this page</strong><span>{message}</span></div></div>; }
