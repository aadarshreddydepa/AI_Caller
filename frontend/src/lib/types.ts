export type Business = { id:string; name:string; slug:string; status:string };
export type Session = { authenticated:boolean; google_enabled:boolean; user:{ id:string; email:string; name:string }; memberships:{ id:string; role:string; business:Business }[] };
export type DashboardData = {
  business:Business;
  calls:{ total:number; completed:number; escalated:number; after_hours:number };
  leads:{ total:number; new:number; converted:number };
  activity:{ date:string; count:number }[];
  recent_calls:Call[];
};
export type Call = { id:string; caller_name:string; caller_phone:string; started_at:string; status:string; duration_seconds:number; escalated:boolean; after_hours:boolean; lead_id:string|null; lead_requirement:string|null };
export type Lead = { id:string; caller_name:string; caller_phone:string; requirement:string; preferred_callback_time:string; urgency:string; status:string; created_at:string };
export type Appointment = { id:string; caller_name:string|null; service_name:string|null; requested_date:string|null; requested_time:string|null; notes:string; status:string; created_at:string };
export type Knowledge = { services:{ id:string; name:string; description:string; price_from:string|null; price_to:string|null; price_note:string; duration_minutes:number|null; active:boolean }[]; faqs:{ id:string; question:string; answer:string; category:string; active:boolean }[] };
export type Notifications = { endpoints:{ id:string; channel:string; destination:string; label:string; enabled:boolean; verified_at:string|null }[]; deliveries:{ id:string; channel:string; destination:string; status:string; attempt_count:number; queued_at:string; sent_at:string|null }[] };
export type BusinessSettings = Business & { legal_name:string; description:string; timezone:string; default_language:string; phone:string; email:string; website:string; service_area:string; escalation_instructions:string };
export type Profile = { id:string; email:string; name:string; phone:string };
