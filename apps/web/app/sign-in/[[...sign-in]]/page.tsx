import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-paper">
      <div className="flex flex-col items-center gap-8">
        <div className="text-center">
          <div className="font-display text-[26px] tracking-tight text-navy">Demo Wealth Advisors</div>
          <div className="mt-1.5 text-[10.5px] font-semibold uppercase tracking-[0.22em] text-gold">
            Plataforma de inteligência
          </div>
        </div>
        <SignIn
          appearance={{
            variables: { colorPrimary: "#0e2a43", borderRadius: "12px" },
          }}
        />
        <p className="max-w-[360px] text-center text-[11px] leading-relaxed text-faint">
          Acesso restrito a profissionais autorizados. Todas as sessões e interações são registradas
          na trilha de auditoria da organização.
        </p>
      </div>
    </div>
  );
}
