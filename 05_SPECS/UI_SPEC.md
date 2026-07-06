# UI_SPEC.md — Especificação de Interface (v1)

| | |
|---|---|
| **Versão** | 1.0 |
| **Data** | 2026-07-03 |
| **Status** | **Aprovado pelo fundador em 2026-07-03** (v1.1, com as 4 decisões do §8 e a diretriz geral de UX incorporadas) — implementação autorizada |
| **Subordinado a** | [PRODUCT_VISION.md](../01_PRODUCT/PRODUCT_VISION.md) (princípios de experiência) · [MVP_SCOPE.md](../01_PRODUCT/MVP_SCOPE.md) (caminho dourado) · [API_SPEC.md](API_SPEC.md) v1.1 |
| **Implementa-se em** | `apps/web` (Next.js) — cada tela referencia os endpoints que consome |

---

## 1. Fundações de design

> **Diretriz geral de UX (fundador, 2026-07-03 — princípio permanente):** em toda decisão de interface, priorizar **clareza, confiança e simplicidade**, no nível de profissionalismo de software de grandes bancos e gestoras. Recursos técnicos, auditoria e complexidade metodológica existem — mas aparecem **apenas quando agregam valor ao profissional**; no restante do tempo, a experiência é limpa, objetiva e focada na tomada de decisão. (Na prática: proveniência a um clique, nunca na cara; auditoria indicada, nunca gritada.)

| Tema | Decisão |
|---|---|
| Tom visual | **Institucional sóbrio**: a linguagem do relatório (navy, dourado discreto, serifada em títulos) estendida ao produto. Nada de fintech colorida — nosso usuário leva nossas telas para a frente de clientes de alto patrimônio |
| Densidade | Alta, profissional: tabelas competentes, tipografia 13–14px em dados, espaçamento funcional. Ferramenta de trabalho diário, não app de consumidor |
| Idioma e formatos | pt-BR institucional; números `1.234.567,89`; datas `dd/mm/aaaa`; percentuais com 2 casas na exibição (4 no hover/proveniência) |
| Plataforma | **Desktop-first** (≥ 1280px); tablet funcional; mobile fora da v1 (o trabalho de preparação acontece em mesa de escritório) |
| Teclado | Atalhos globais: `g h` home · `g f` famílias · `/` busca · `?` ajuda de atalhos. Toda ação primária alcançável sem mouse |
| Acessibilidade | WCAG 2.1 AA como piso: contraste, foco visível, navegação por teclado, labels |
| Anti-padrões proibidos | Emojis na interface · gamificação/confete · notificações de engajamento · dark patterns de upgrade · qualquer elemento que constranja o profissional em tela compartilhada com cliente |

## 2. Arquitetura de informação

```
Home (Mesa de Reuniões)                         ← a agenda é a home, não um dashboard
├── Famílias
│    └── Família (detalhe)
│         ├── Carteira consolidada              ← posições, selos, alocação, liquidez
│         ├── Reuniões (linha do tempo)
│         ├── Documentos e conexões
│         └── Análises (runs)
├── Reunião (workspace)                         ← a tela central do produto
├── Caixa de confirmação                        ← extrações aguardando conferência
├── Configurações (organização, equipe, política, benchmarks, marca, retenção IA)
└── Auditoria (trilha filtrável)
```

## 3. Telas do caminho dourado

### S1 — Onboarding (meta: valor em 30 minutos)
Passos: criar organização → subir logo/cores (preview do relatório em tempo real — o momento "isso é meu") → convidar equipe (opcional, pulável) → criar primeira família → conectar dados (Open Finance **ou** upload de extrato **ou** manual — os três caminhos lado a lado, sem hierarquia de culpa) → primeira análise disparada automaticamente. Barra de progresso honesta; tudo pulável exceto organização e família.

### S2 — Home: Mesa de Reuniões
Ao abrir a plataforma, o profissional sabe imediatamente (decisão do fundador, §8.1): **reuniões de hoje · análises pendentes · carteiras que precisam de revisão · alertas de risco · tarefas pendentes.**
- **Coluna principal:** reuniões de hoje e próximas, ordenadas por data, cada cartão com: família, data, chip de estado (§5), resumo de pontos de atenção do último run (`3 pontos · 1 alta`), ação primária contextual ("Preparar" / "Gerar material" / "Marcar realizada").
- **Coluna lateral:** *Precisa da sua atenção*, agrupada em: **Análises pendentes** (extrações aguardando confirmação, contratos incompletos) · **Carteiras para revisão** (dados defasados, selos C/D) · **Alertas de risco** (concentração/FGC do último run) · **Tarefas** (vencimentos próximos, follow-ups).
- **Vazio-estado** (primeiro uso): guia os 3 passos restantes do onboarding, nunca uma tela em branco.
- Consome: `GET /families/*/meetings`, `GET /audit-events` (pendências), `GET /documents?status=awaiting_confirmation`.

### S3 — Família: carteira consolidada
- Cabeçalho: patrimônio total, retorno vs. benchmark da família (regra do %CDI negativo aplicada), data-base, **selo de confiança agregado**.
- Tabela de posições (agrupável por conta/classe/titular): ativo, titular, classe, indexador, vencimento, valor, selo A–D. **Toda célula numérica é clicável → gaveta de proveniência (§5)**.
- Painéis: alocação por classe (barras), escada de liquidez, concentrações (visão família + FGC por titular, lado a lado — decisão DOMAIN_MODEL 9.1).
- Posições de classe não suportada: linha visível com badge "fora das métricas — limitação declarada", nunca ocultas.
- Consome: `GET /accounts/*/positions`, `GET /analysis-runs/{id}`.

### S4 — Caixa de confirmação (extração)
- Lista de documentos aguardando; ao abrir: **visão lado a lado** — página do PDF original à esquerda, posições extraídas à direita, célula a célula editável.
- Divergências e campos ausentes destacados; contrato incompleto abre o **formulário de complementação** inline (principal, taxa, data, aniversário — decisão 9.3), marcando origem `user_provided` visivelmente.
- Ações: confirmar tudo · corrigir e confirmar · rejeitar. Confirmação exibe resumo do que entrará no motor. Nada entra sem passar por aqui.
- Consome: `GET /documents/{id}/extraction`, `POST .../confirm`, `POST /positions/{id}/contract-terms`.

### S5 — Workspace de Reunião (a tela central do produto)
Layout em três zonas:
1. **Cabeçalho de estado:** família, data, os 6 estados como jornada visual (chips), transições permitidas como botões; pulo de estado pede confirmação leve e avisa que será auditado ("Registrar como realizada sem material? A exceção ficará na trilha").
2. **Painel de preparação (centro):** abas *Briefing* (resumo executivo + o-que-mudou + pauta sugerida, gerados do run com `validator_result` visível) · *Pontos de atenção* (cards por severidade, cada um expansível até o número de origem) · *Carteira* (S3 embutida).
3. **Trilho de material (direita):** versões do material com autor/data/parâmetros; `material_sent` congela (cadeado + tooltip explicando); regenerar cria v2 preservando v1 (decisão API 9.2); botão de download/envio.
4. **Dock de Q&A (inferior, recolhível):** pergunta → resposta fundamentada no run, com proveniência. Registro em auditoria indicado por **ícone discreto com tooltip** (decisão do fundador §8.3: o usuário sabe, sem intrusão; o detalhe vive nos termos de uso).
- Consome: `GET /meetings/{id}`, `POST .../transition`, `POST .../materials`, `POST /analysis-runs/{id}/generations|qa`.

### S6 — Editor de material
- Preview fiel do relatório (a marca do escritório aplicada); **texto da narrativa editável** (edições viram `GenerationEdit`, auditadas); **números não editáveis** — para alterar um número, corrige-se o dado de origem e regenera-se (trava de integridade I1 na interface).
- Nota metodológica e disclaimers: visíveis no preview, não removíveis.

### S7 — Configurações
Organização e marca · Equipe (papéis admin/professional; compartilhamentos por família — decisão API 9.4) · **Política de limiares** (formulário dos parâmetros com defaults; salvar = nova versão; histórico de versões visível — nunca edição in-place) · Benchmarks da casa · Retenção de registros de IA (dias; nulo = indefinida; alerta sobre implicações de conformidade).

### S8 — Auditoria
Tabela filtrável (tipo, entidade, autor, período) consumindo `GET /audit-events`; linha expansível com payload; exportação CSV. É a tela que se mostra a um auditor externo — sobriedade máxima.

## 4. Padrões globais

- **Gaveta de proveniência** (o padrão que define o produto): clicar em qualquer número abre painel lateral com: valor completo (4 casas) · como foi calculado (metodologia em uma frase + link para a nota) · dados de origem (transações/preços com fonte e data) · run, versão do motor e versão da política · selo de confiança. Do relatório à transação em dois cliques.
- **Selos de confiança A–D:** pastilhas discretas (verde/azul/âmbar/vermelho) com tooltip padronizado; presentes em toda posição, herdados por análises.
- **Limitações declaradas:** faixa fina e sóbria no topo de análises afetadas ("Esta análise exclui 1 posição de classe não suportada — ver detalhes"), nunca modal, nunca escondida.
- **Erros:** Problem Details → mensagem humana + código discreto (`CONTRACT_TERMS_MISSING` vira "Faltam dados do contrato para calcular esta posição — completar agora?" com ação).
- **Estados de carregamento:** skeletons; análises longas mostram progresso real do run, nunca spinner infinito.

## 5. Chips de estado da reunião

`Agendada` (cinza) → `Em preparação` (azul) → `Material gerado` (índigo) → `Material enviado` (dourado + cadeado no material) → `Realizada` (verde) · `Cancelada` (cinza riscado). Sempre com data da última transição; pulos exibem marcador de exceção na linha do tempo.

## 6. Fora da v1 (recusas de interface)

Dashboard de mercado/cotações · feed de notícias · modo apresentação (v1.1) · app mobile · personalização de layout · temas (dark mode avaliado na v1.1) · white-label da interface (anti-objetivo) · onboarding com tour forçado.

## 7. Critérios de aceite da interface

Caminho dourado completo sem mouse exceto upload · valor em ≤ 30 min do cadastro (medido no onboarding) · nenhum número sem proveniência acessível · nenhuma tela vazia sem orientação · relatório com marca do escritório indistinguível de material feito por analista sênior (teste com os extratos reais do fundador).

## 8. Decisões do fundador (revisão de prática, 2026-07-03)

1. **Home = produtividade, sem pulso de mercado — aprovado.** Ao abrir: reuniões de hoje, análises pendentes, carteiras a revisar, alertas de risco, tarefas. Módulo de mercado (notícias/indicadores/cotações) registrado como possibilidade futura que **não pode competir** com o objetivo principal.
2. **Números nunca editáveis — aprovado totalmente.** Alteração sempre na origem do dado + nova geração. "A confiança na plataforma depende de que os relatórios sejam sempre reproduzíveis e auditáveis."
3. **Auditoria do Q&A indicada discretamente — aprovado com ajuste:** ícone discreto + termos de uso; sem aviso intrusivo permanente.
4. **Relatório do cliente limpo — aprovado:** nota metodológica resumida no material; detalhes completos (fontes, selos por posição, versões, trilha) apenas na área interna para profissionais autorizados.

**Diretriz geral de UX registrada como princípio permanente** (ver §1): clareza, confiança e simplicidade em nível de software de grandes bancos; complexidade técnica visível apenas quando agrega valor.

**Changelog:** v1.0 (2026-07-03) — versão inicial para aprovação. · v1.1 (2026-07-03) — aprovada com as 4 decisões e a diretriz geral de UX incorporadas (§1, §3, §8).
