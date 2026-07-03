# SECURITY_COMPLIANCE.md — Segurança e Conformidade

| | |
|---|---|
| **Versão** | 1.0 |
| **Data** | 2026-07-03 |
| **Status** | Final (delegação total; ciclo rascunho → autocrítica → revisão aplicado) |
| **Subordinado a** | [MISSION.md](../00_FOUNDATION/MISSION.md) · [ARCHITECTURE.md](ARCHITECTURE.md) (I3, I4) |

---

## 1. Postura

Guardamos o dado mais sensível que existe depois de saúde: **o patrimônio detalhado de famílias**. Para um bootstrap, a tentação é "segurança depois" — recusada: um vazamento na Fase 1 não é um incidente, é o fim da empresa (confiança é o produto). A contrapartida pragmática: fazemos **bem o essencial** agora e certificações depois — sem teatro de compliance.

## 2. Segurança de aplicação e infraestrutura (Fase 1 — obrigatório)

- **Isolamento de tenant:** RLS no Postgres + filtro na aplicação (defesa em profundidade, I3); **suíte de testes de isolamento** (tentativas de acesso cruzado entre tenants de teste) rodando em todo release — o teste que nunca pode falhar.
- **Autenticação:** provedor gerenciado (Clerk), MFA obrigatório para todos os usuários (não opcional — mercado fiduciário), sessões com expiração, papéis mínimos (admin/profissional).
- **Criptografia:** TLS em trânsito; at-rest nativo do provedor; segredos exclusivamente em vault da plataforma (nunca em código/repositório — verificação automática de vazamento de segredos no CI).
- **Menor privilégio:** credenciais de banco distintas por serviço; a permissão de UPDATE/DELETE no esquema `audit` é revogada no nível do banco (I4 imposta por permissão, não por disciplina).
- **Dependências:** verificação automática de vulnerabilidades (Dependabot/audit) com política de correção ≤ 7 dias para críticas.
- **Backups:** diários, retenção 35 dias, **teste de restauração mensal documentado** (backup sem teste de restore é superstição).
- **Logs estruturados** com trilha de acesso a dados (quem viu a carteira de quem, quando) — parte do produto (P3), não só de segurança.

## 3. LGPD (mínimo viável correto — Fase 1)

| Item | Implementação |
|---|---|
| Papéis | Escritório = controlador; nós = operador. Contrato de operador (DPA) anexo ao contrato comercial desde o design partner nº 1 |
| Base legal | Execução de contrato (dados dos profissionais); legítimo interesse/execução contratual do controlador (dados dos clientes finais dele) — parecer jurídico na Fase 1 confirma o enquadramento |
| Minimização | Só coletamos o que a análise exige (DATA_STRATEGY §7); campos "seria bom ter" não existem no schema |
| Direitos do titular | Exportação e exclusão por família/cliente operáveis pelo escritório na própria plataforma; prazo de rescisão: purga ≤ 30 dias (backups ≤ 90) |
| Encarregado (DPO) | Fundador, nomeado formalmente; e-mail dedicado publicado |
| RIPD | Relatório de impacto elaborado na Fase 1 (o processamento de dados patrimoniais o justifica) |
| Suboperadores | Lista pública e contratualizada: cloud (região BR), Anthropic (IA — sem retenção para treino), agregador Open Finance, Clerk, observabilidade. Mudança de lista = notificação aos controladores |
| Incidentes | Runbook: contenção → avaliação → notificação à ANPD e controladores em prazo legal → post-mortem público interno. Simulação anual |

## 4. Fronteira regulatória CVM (o que a plataforma é e não é)

- **Somos software de análise** para profissionais registrados — não prestamos consultoria de valores mobiliários (Res. CVM 19/21), não somos analistas (Res. 20/21), não administramos carteiras (Res. 21/21). A responsabilidade da recomendação é integralmente do profissional usuário — e o produto é desenhado para *reforçar* isso (linguagem descritiva imposta pelo verificador — AI_ARCHITECTURE §3; telas de análise com atribuição clara ao profissional).
- **Parecer jurídico especializado na Fase 1** valida o enquadramento e os disclaimers padrão dos relatórios (custo estimado R$ 15–30 mil, único gasto jurídico relevante do ano — vale cada centavo: é a licença social do negócio).
- **Monitoramento regulatório contínuo** (agente de pesquisa trimestral): diretrizes CVM sobre IA esperadas em 2026+ (Crença C4) — nossa trilha de auditoria de IA já nasce em conformidade com o que se desenha (documentação, supervisão humana, explicabilidade).
- **Cláusula de uso aceitável:** contrato proíbe uso da plataforma para distribuir recomendações automatizadas ao público (protege o cliente e a nós).

## 5. O que fica para depois (explicitamente adiado, com gatilho)

| Item | Gatilho para fazer |
|---|---|
| Pentest externo | Antes do 1º cliente Instituição ou Gate 2→3, o que vier primeiro |
| SOC 2 / ISO 27001 | Exigência contratual de cliente enterprise (Fase 3) — postura desde já: controles documentados como se fôssemos auditar |
| SSO/SAML | Plano Instituição (já previsto no BUSINESS_MODEL) |
| Seguro cyber | Avaliar no Gate 1→2 |
| Infra dedicada por cliente | Nunca, salvo contrato que pague por isso (ARCHITECTURE §6) |

**Changelog:** v1.0 (2026-07-03) — versão inicial sob delegação total.
