export function initials(name:string) { return name.split(/\s+/).filter(Boolean).slice(0,2).map(part => part[0]).join("").toUpperCase() || "U"; }
export function displayName(name:string, email:string) { return name || email.split("@")[0]; }
