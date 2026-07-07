import Image from "next/image";
import Link from "next/link";

const CONTACT_EMAIL = "joaopedroprista@gmail.com";
const DEMO_MAILTO = `mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent(
  "Quero conhecer a plataforma"
)}`;

const PILLARS = [
  {
    title: "Motor determinístico",
    body: "Todo número — retorno, risco, concentração — nasce de cálculo auditável. A IA nunca faz aritmética; ela traduz o que o motor já calculou.",
  },
  {
    title: "Trilha de auditoria completa",
    body: "Cada análise é reproduzível: mesma carteira, mesma versão do motor, mesmo resultado — para sempre. Rastreável até a transação de origem.",
  },
  {
    title: "Neutralidade",
    body: "Não distribuímos produtos, não recebemos rebates, não competimos com o seu negócio. Vendemos software; a confiança é do profissional.",
  },
];

const FEATURES = [
  {
    title: "Análise institucional automática",
    body: "Retorno, risco, atribuição e custos — calculados no padrão de uma equipe de análise, em minutos.",
    icon: IconChart,
  },
  {
    title: "Preparação de reunião",
    body: "Briefing pronto, pauta sugerida e o que mudou desde o último encontro com o cliente.",
    icon: IconCalendar,
  },
  {
    title: "Radar de Consenso",
    body: "O que as maiores gestoras do mundo detêm e mudaram — direto das declarações regulatórias públicas.",
    icon: IconRadar,
  },
  {
    title: "Trilha de auditoria",
    body: "Todo número clicável até a fonte: transação, preço, versão do motor e da política aplicada.",
    icon: IconShield,
  },
  {
    title: "Compliance nativo",
    body: "Linguagem sempre descritiva, nunca prescritiva — desenhado para a fronteira regulatória da CVM.",
    icon: IconCheck,
  },
];

const AUDIENCE = [
  "Consultorias de valores mobiliários (CVM)",
  "Wealth managers e assessores independentes",
  "Multi family offices",
];

const FAQ = [
  {
    q: "A plataforma recomenda investimentos?",
    a: "Não. O motor calcula, a IA traduz os números em linguagem clara — a recomendação é sempre do profissional, que responde por ela. É uma escolha de design, não uma limitação técnica.",
  },
  {
    q: "Os dados dos meus clientes ficam seguros?",
    a: "Sim. Isolamento por organização, criptografia em trânsito e em repouso, e dados de clientes nunca são usados para treinar modelos ou vendidos a terceiros.",
  },
  {
    q: "Preciso trocar de custodiante?",
    a: "Não. A ingestão funciona com o que você já usa hoje: Open Finance quando disponível, upload de extrato quando não — com conferência humana antes de qualquer número entrar na análise.",
  },
  {
    q: "Quanto custa?",
    a: "Planos por profissional e por organização, sem cobrança sobre patrimônio (AUM). Fale com a gente para conhecer os valores e o programa de escritórios fundadores.",
  },
];

export default function MarketingHome() {
  return (
    <div id="top" className="bg-paper">
      <header className="sticky top-0 z-30 border-b border-hairline bg-paper/90 backdrop-blur-sm">
        <div className="mx-auto flex max-w-[1180px] items-center justify-between px-6 py-4">
          <div className="flex items-baseline gap-2">
            <span className="font-display text-[19px] tracking-tight text-navy">Cerne</span>
            <span className="hidden text-[11px] text-faint sm:inline">— inteligência de carteiras</span>
          </div>
          <nav className="hidden items-center gap-7 text-[13.5px] text-muted md:flex">
            <a href="#produto" className="hover:text-navy">Produto</a>
            <a href="#como-funciona" className="hover:text-navy">Como funciona</a>
            <a href="#faq" className="hover:text-navy">Perguntas frequentes</a>
          </nav>
          <div className="flex items-center gap-3">
            <Link href="/sign-in" className="text-[13.5px] font-medium text-navy hover:underline">
              Entrar
            </Link>
            <a
              href={DEMO_MAILTO}
              className="rounded-full bg-navy px-4 py-2 text-[13px] font-medium text-white shadow-card transition-colors hover:bg-navy-deep"
            >
              Agendar demonstração
            </a>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="mx-auto max-w-[1180px] px-6 pb-8 pt-16 md:pt-24">
        <div className="grid items-center gap-14 md:grid-cols-2">
          <div>
            <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-gold-soft px-3 py-1 text-[11.5px] font-medium text-gold">
              Para consultorias, wealth managers e family offices
            </div>
            <h1 className="font-display text-[38px] leading-[1.12] tracking-tight text-navy md:text-[46px]">
              A inteligência institucional por trás de cada reunião com seu cliente
            </h1>
            <p className="mt-5 max-w-[480px] text-[16px] leading-relaxed text-ink/75">
              A Cerne transforma a carteira dos seus clientes em análise pronta para a reunião —
              em minutos, com todo número auditável. Sem recomendação automática: você continua
              no centro da decisão.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-4">
              <a
                href={DEMO_MAILTO}
                className="rounded-full bg-navy px-6 py-3 text-[14px] font-medium text-white shadow-card transition-colors hover:bg-navy-deep"
              >
                Agendar demonstração
              </a>
              <a href="#como-funciona" className="text-[14px] font-medium text-navy hover:underline">
                Ver como funciona ↓
              </a>
            </div>
          </div>
          <div className="relative">
            <div className="overflow-hidden rounded-2xl border border-hairline bg-surface shadow-card-hover">
              <div className="flex items-center gap-1.5 border-b border-hairline bg-paper px-4 py-2.5">
                <span className="h-2.5 w-2.5 rounded-full bg-bad/40" />
                <span className="h-2.5 w-2.5 rounded-full bg-warn/40" />
                <span className="h-2.5 w-2.5 rounded-full bg-ok/40" />
              </div>
              <Image
                src="/marketing/hero-workspace.png"
                alt="Workspace de reunião da plataforma, com briefing, KPIs e pontos de atenção"
                width={1440}
                height={950}
                className="w-full"
                priority
              />
            </div>
            <p className="mt-3 text-center text-[11.5px] text-faint">
              Tela real da plataforma — dados de demonstração
            </p>
          </div>
        </div>
      </section>

      {/* Por que existimos */}
      <section className="border-t border-hairline bg-surface">
        <div className="mx-auto max-w-[1180px] px-6 py-20">
          <div className="max-w-[640px]">
            <div className="mb-3 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-gold">
              <span>→</span> Por que existimos
            </div>
            <h2 className="font-display text-[30px] leading-tight text-navy">
              Nascemos da rotina de quem já viveu a dor
            </h2>
            <p className="mt-4 text-[15px] leading-relaxed text-ink/75">
              Horas reconciliando posições, montando material em PowerPoint, torcendo para não
              errar um número na frente do cliente. A Cerne existe para devolver esse tempo ao
              profissional — sem abrir mão do rigor que o dever fiduciário exige.
            </p>
          </div>
          <div className="mt-12 grid gap-8 md:grid-cols-3">
            {PILLARS.map((p) => (
              <div key={p.title} className="border-t-2 border-navy pt-4">
                <h3 className="font-display text-[18px] text-navy">{p.title}</h3>
                <p className="mt-2 text-[13.5px] leading-relaxed text-ink/70">{p.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Produto / features */}
      <section id="produto" className="border-t border-hairline">
        <div className="mx-auto max-w-[1180px] px-6 py-20">
          <div className="mb-3 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-gold">
            <span>→</span> O que a plataforma faz
          </div>
          <h2 className="max-w-[560px] font-display text-[30px] leading-tight text-navy">
            Da carteira à reunião, sem planilha no meio do caminho
          </h2>
          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-5">
            {FEATURES.map((f) => (
              <div key={f.title} className="rounded-2xl border border-hairline bg-surface p-6 shadow-card">
                <f.icon className="h-6 w-6 text-gold" />
                <h3 className="mt-4 text-[14.5px] font-semibold text-navy">{f.title}</h3>
                <p className="mt-2 text-[12.5px] leading-relaxed text-ink/70">{f.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Como funciona / diferencial */}
      <section id="como-funciona" className="border-t border-hairline bg-navy">
        <div className="mx-auto grid max-w-[1180px] items-center gap-14 px-6 py-20 md:grid-cols-2">
          <div>
            <div className="mb-3 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-gold">
              <span>→</span> Como funciona
            </div>
            <h2 className="font-display text-[30px] leading-tight text-white">
              O motor calcula. A IA traduz. Você recomenda.
            </h2>
            <p className="mt-4 text-[15px] leading-relaxed text-white/70">
              É a nossa linha vermelha, por desenho: nenhum número apresentado nasce de um modelo
              generativo, e a plataforma nunca recomenda em nome próprio. O resultado é uma
              ferramenta que reforça — nunca substitui — o profissional que responde pela decisão
              perante o cliente e o regulador.
            </p>
            <ul className="mt-6 space-y-3 text-[14px] text-white/85">
              <li className="flex items-start gap-2.5">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-gold" />
                Compatível com a Resolução CVM 19/21 — análise descritiva, não consultoria automatizada
              </li>
              <li className="flex items-start gap-2.5">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-gold" />
                Cada texto gerado é auditado: modelo, versão e run de origem
              </li>
              <li className="flex items-start gap-2.5">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-gold" />
                Limitações sempre declaradas — nunca escondidas atrás de um número bonito
              </li>
            </ul>
          </div>
          <div className="overflow-hidden rounded-2xl border border-white/10 shadow-card-hover">
            <Image
              src="/marketing/radar.png"
              alt="Radar de Consenso mostrando posições reais de grandes gestoras globais"
              width={1440}
              height={1500}
              className="w-full"
            />
          </div>
        </div>
      </section>

      {/* Para quem é */}
      <section className="border-t border-hairline">
        <div className="mx-auto max-w-[1180px] px-6 py-20">
          <div className="grid items-start gap-14 md:grid-cols-2">
            <div>
              <div className="mb-3 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-gold">
                <span>→</span> Feita para quem vive de confiança
              </div>
              <h2 className="font-display text-[30px] leading-tight text-navy">Para quem é a Cerne</h2>
              <ul className="mt-6 space-y-3">
                {AUDIENCE.map((a) => (
                  <li key={a} className="flex items-center gap-3 text-[15px] text-ink/80">
                    <IconCheck className="h-5 w-5 shrink-0 text-gold" />
                    {a}
                  </li>
                ))}
              </ul>
              <a
                href={DEMO_MAILTO}
                className="mt-8 inline-block rounded-full bg-navy px-6 py-3 text-[14px] font-medium text-white shadow-card transition-colors hover:bg-navy-deep"
              >
                Fale com a gente sobre planos
              </a>
            </div>
            <div className="rounded-2xl border border-hairline bg-gold-soft p-8">
              <p className="font-display text-[19px] leading-snug text-navy">
                &ldquo;Estamos em fase de validação com um grupo pequeno de escritórios
                fundadores.&rdquo;
              </p>
              <p className="mt-4 text-[13.5px] leading-relaxed text-ink/70">
                Preferimos isso a estatísticas infladas: nenhum número de patrimônio ou de clientes
                nesta página é fabricado. Quando tivermos histórico real para mostrar, ele estará
                aqui — com a mesma trilha de auditoria que aplicamos às suas carteiras.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="border-t border-hairline bg-surface">
        <div className="mx-auto max-w-[820px] px-6 py-20">
          <div className="mb-3 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-gold">
            <span>→</span> Perguntas frequentes
          </div>
          <h2 className="font-display text-[28px] leading-tight text-navy">
            O que profissionais como você perguntam primeiro
          </h2>
          <div className="mt-10 divide-y divide-hairline">
            {FAQ.map((item) => (
              <div key={item.q} className="py-6">
                <h3 className="text-[15px] font-semibold text-navy">{item.q}</h3>
                <p className="mt-2 text-[13.5px] leading-relaxed text-ink/70">{item.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-hairline bg-navy-deep">
        <div className="mx-auto max-w-[1180px] px-6 py-16">
          <div className="flex flex-col items-start justify-between gap-10 md:flex-row">
            <div className="max-w-[340px]">
              <span className="font-display text-[19px] text-white">Cerne</span>
              <p className="mt-3 text-[13px] leading-relaxed text-white/60">
                Inteligência institucional para quem prepara cada reunião de investimento. Motor
                determinístico, trilha de auditoria completa, neutralidade sempre.
              </p>
            </div>
            <div className="flex gap-16">
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-wider text-white/40">Produto</div>
                <div className="mt-3 flex flex-col gap-2 text-[13.5px] text-white/70">
                  <a href="#produto" className="hover:text-white">O que a plataforma faz</a>
                  <a href="#como-funciona" className="hover:text-white">Como funciona</a>
                  <a href="#faq" className="hover:text-white">Perguntas frequentes</a>
                </div>
              </div>
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-wider text-white/40">Contato</div>
                <div className="mt-3 flex flex-col gap-2 text-[13.5px] text-white/70">
                  <a href={DEMO_MAILTO} className="hover:text-white">{CONTACT_EMAIL}</a>
                  <Link href="/sign-in" className="hover:text-white">Entrar na plataforma</Link>
                </div>
              </div>
            </div>
          </div>
          <div className="mt-12 border-t border-white/10 pt-6 text-[11.5px] text-white/40">
            © {new Date().getFullYear()} Cerne. Software de análise — não somos corretora,
            distribuidora nem consultoria de valores mobiliários.
          </div>
        </div>
      </footer>

      <a
        href="#top"
        className="fixed bottom-6 right-6 z-40 flex h-11 w-11 items-center justify-center rounded-full bg-navy text-white shadow-card-hover transition-colors hover:bg-navy-deep"
        aria-label="Voltar ao topo"
      >
        ↑
      </a>
    </div>
  );
}

function IconChart({ className = "" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 19V9M11 19V5M18 19v-6" />
      <path d="M3 19h18" />
    </svg>
  );
}
function IconCalendar({ className = "" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <rect x="3.5" y="5" width="17" height="15.5" rx="2.5" />
      <path d="M3.5 9.5h17M8 3v3.5M16 3v3.5" />
    </svg>
  );
}
function IconRadar({ className = "" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <circle cx="12" cy="12" r="8.5" />
      <circle cx="12" cy="12" r="4.5" />
      <path d="M12 12l5.5-5.5" />
      <circle cx="12" cy="12" r="0.8" fill="currentColor" />
    </svg>
  );
}
function IconShield({ className = "" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3.5 5 6v5.5c0 4.4 3 7.6 7 9 4-1.4 7-4.6 7-9V6l-7-2.5Z" />
      <path d="m9.2 12 2 2 3.6-3.8" />
    </svg>
  );
}
function IconCheck({ className = "" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="9" />
      <path d="m8 12.5 2.5 2.5L16 9.5" />
    </svg>
  );
}
