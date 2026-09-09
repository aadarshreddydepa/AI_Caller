export function PageHeader({ title, subtitle, eyebrow="AI CALLER WORKSPACE", action }:{ title:string; subtitle:string; eyebrow?:string; action?:React.ReactNode }) {
  return <section className="page-heading"><div><p>{eyebrow}</p><h1>{title}</h1><span>{subtitle}</span></div>{action}</section>;
}
