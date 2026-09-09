import { WorkspaceShell } from "@/components/layout/workspace-shell";
import { WorkspaceProvider } from "@/providers/workspace-provider";
export default function DashboardLayout({ children }:{ children:React.ReactNode }) { return <WorkspaceProvider><WorkspaceShell>{children}</WorkspaceShell></WorkspaceProvider>; }
