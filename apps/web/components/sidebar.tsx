"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { UserButton } from "@clerk/nextjs";

export function Sidebar({ pendingCount = 0 }: { pendingCount?: number }) {
  const pathname = usePathname();
  const nav = [
    { label: "Mesa de Reuniões", href: "/app", match: (p: string) => p === "/app" || p.startsWith("/app/reunioes"), icon: IconCalendar },
    { label: "Radar de Consenso", href: "/app/radar", match: (p: string) => p.startsWith("/app/radar"), icon: IconRadar },
    { label: "Famílias", href: "/app/familias", match: (p: string) => p.startsWith("/app/familias"), icon: IconUsers },
    { label: "Caixa de confirmação", href: "/app/caixa-de-confirmacao", match: (p: string) => p.startsWith("/app/caixa-de-confirmacao"), icon: IconInbox, badge: pendingCount || undefined },
    { label: "Configurações", href: "/app/configuracoes", match: (p: string) => p.startsWith("/app/configuracoes"), icon: IconSettings },
    { label: "Auditoria", href: "/app/auditoria", match: (p: string) => p.startsWith("/app/auditoria"), icon: IconShield },
  ];
  return (
    <aside className="sticky top-0 flex h-screen w-64 shrink-0 flex-col bg-gradient-to-b from-navy-deep to-navy text-white/80">
      <div className="px-6 pt-7 pb-6">
        <div className="font-display text-[17px] tracking-tight text-white">
          Demo Wealth Advisors
        </div>
        <div className="mt-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-gold">
          Plataforma de inteligência
        </div>
      </div>

      <nav className="mt-1 flex flex-col gap-0.5 px-3">
        {nav.map((item) => {
          const active = item.match(pathname);
          return (
            <Link
              key={item.label}
              href={item.href}
              className={`group flex items-center gap-3 rounded-lg px-3 py-2.5 text-[13.5px] transition-colors ${
                active ? "bg-white/10 font-medium text-white" : "hover:bg-white/5 hover:text-white"
              }`}
            >
              <item.icon className={active ? "text-gold" : "text-white/40 group-hover:text-white/70"} />
              <span className="flex-1">{item.label}</span>
              {item.badge && (
                <span className="rounded-full bg-gold px-2 py-0.5 text-[10.5px] font-semibold text-navy-deep">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto border-t border-white/10 px-6 py-5">
        <div className="flex items-center gap-3">
          <UserButton
            appearance={{ elements: { avatarBox: "h-9 w-9 ring-2 ring-gold/70" } }}
          />
          <div className="min-w-0">
            <div className="truncate text-[13px] font-medium text-white">Sua conta</div>
            <div className="text-[11px] text-white/50">Sessão auditada</div>
          </div>
        </div>
      </div>
    </aside>
  );
}

function IconRadar({ className = "" }: { className?: string }) {
  return (
    <svg className={`h-[17px] w-[17px] ${className}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <circle cx="12" cy="12" r="8.5" />
      <circle cx="12" cy="12" r="4.5" />
      <path d="M12 12l5.5-5.5" />
      <circle cx="12" cy="12" r="0.8" fill="currentColor" />
    </svg>
  );
}

function IconCalendar({ className = "" }: { className?: string }) {
  return (
    <svg className={`h-[17px] w-[17px] ${className}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <rect x="3.5" y="5" width="17" height="15.5" rx="2.5" />
      <path d="M3.5 9.5h17M8 3v3.5M16 3v3.5" />
    </svg>
  );
}
function IconUsers({ className = "" }: { className?: string }) {
  return (
    <svg className={`h-[17px] w-[17px] ${className}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <circle cx="9" cy="8.5" r="3.2" />
      <path d="M3.5 19.5c.8-3 2.9-4.5 5.5-4.5s4.7 1.5 5.5 4.5M15.5 5.6a3.2 3.2 0 0 1 0 5.8M17.5 15.3c1.6.6 2.6 1.9 3 4.2" />
    </svg>
  );
}
function IconInbox({ className = "" }: { className?: string }) {
  return (
    <svg className={`h-[17px] w-[17px] ${className}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3.5 13.5 6 5.5h12l2.5 8M3.5 13.5V18a1.5 1.5 0 0 0 1.5 1.5h14a1.5 1.5 0 0 0 1.5-1.5v-4.5M3.5 13.5H9a3 3 0 0 0 6 0h5.5" />
    </svg>
  );
}
function IconSettings({ className = "" }: { className?: string }) {
  return (
    <svg className={`h-[17px] w-[17px] ${className}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M12 3.5v2.2M12 18.3v2.2M20.5 12h-2.2M5.7 12H3.5M18 6l-1.6 1.6M7.6 16.4 6 18M18 18l-1.6-1.6M7.6 7.6 6 6" />
    </svg>
  );
}
function IconShield({ className = "" }: { className?: string }) {
  return (
    <svg className={`h-[17px] w-[17px] ${className}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3.5 5 6v5.5c0 4.4 3 7.6 7 9 4-1.4 7-4.6 7-9V6l-7-2.5Z" />
      <path d="m9.2 12 2 2 3.6-3.8" />
    </svg>
  );
}
