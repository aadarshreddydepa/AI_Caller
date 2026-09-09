"use client";
import { OverviewDashboard } from "@/components/dashboard/overview-dashboard";
import { PageError, PageLoading } from "@/components/ui/states";
import { useApi } from "@/hooks/use-api";
import type { DashboardData } from "@/lib/types";
import { useWorkspace } from "@/providers/workspace-provider";
export default function OverviewPage() { const { session, businessId } = useWorkspace(); const { data, error } = useApi<DashboardData>(`/backend/api/v1/businesses/${businessId}/dashboard/`); if (error) return <PageError message={error}/>; if (!data) return <PageLoading/>; return <OverviewDashboard session={session} data={data}/>; }
