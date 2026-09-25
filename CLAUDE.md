# CLAUDE.md — economistarenato.com.br

> Arquivo de contexto para o Claude Code. Coloque-o na **raiz do repositório**
> (`economistarenato/CLAUDE.md`). O Claude Code lê este arquivo automaticamente
> ao iniciar e o usa como memória permanente do projeto.

---

## 1. O que é este projeto

Site institucional de **Renato Wanderley Gomes** — economista (CORECON-MS nº 1297),
sócio-fundador da WGSA Gestão Empresarial e pré-candidato ao Governo de Mato Grosso
do Sul pelo partido Democracia Cristã (DC).

O site funciona como vitrine de **análises técnicas de economia e finanças públicas
do MS**, com um painel de dados/indicadores que pode ser atualizado de forma simples.
Não é um blog populista: o registro é o de **economista institucional**, com toda
afirmação ancorada em fonte primária verificável (Portal da Transparência, LOA,
Diário Oficial, SICONFI/RREO, IBGE, MDIC etc.).

**Domínio oficial:** `economistarenato.com.br`
**Handle público:** `@economistarenato`

---

## 2. Stack e arquitetura

- **Site estático** — HTML/CSS/JS puro, sem framework, sem build step.
- **Dados dinâmicos** — o `index.html` lê um JSON (`dados/indicadores.json`) em
  tempo de execução e renderiza o painel de indicadores. Para atualizar números,
  edita-se o JSON; o HTML não muda.
- **Atualização de dados** — script Python opcional (`scripts/atualiza_dados.py`)
  para coletar/preencher os indicadores.
- **Hospedagem** — Netlify, com deploy contínuo a partir do GitHub.
- **Sem CMS, sem servidor, sem banco de dados.** Edita-se arquivo → `git push` →
  Netlify publica em ~1 minuto.

---

## 3. Estrutura do repositório

```
economistarenato/
├── dados/
│   └── indicadores.json      # PAINEL DE DADOS — edite aqui para atualizar números
├── scripts/
│   └── atualiza_dados.py      # coleta/atualização automática de indicadores
├── site/
│   └── index.html             # site completo (responsivo, lê o JSON dinamicamente)
├── netlify.toml               # config de hospedagem + headers de segurança
├── README.md                  # guia de publicação
└── CLAUDE.md                  # este arquivo
```

> **Atenção:** o diretório publicado pelo Netlify é `site/` (publish directory).
> O `index.html` fica em `site/index.html`, **não** na raiz.

---

## 4. Hospedagem e domínio (estado atual)

| Item | Valor |
|------|-------|
| Repositório GitHub | `renatogomes-afk/economistarenato` (branch `main`) |
| Plataforma | Netlify |
| URL provisória Netlify | `wondrous-twilight-d6880e.netlify.app` |
| Domínio | `economistarenato.com.br` (registrado no Registro.br, ~R$40/ano) |
| DNS gerenciado por | Registro.br (não usa Netlify DNS) |
| Registro A (`@`) | `75.2.60.5` (IP load balancer do Netlify) |
| Registro CNAME (`www`) | `wondrous-twilight-d6880e.netlify.app` |

**Config do Netlify (Build & deploy):**
- Branch to deploy: `main`
- Base directory: *(vazio)*
- Build command: *(vazio)*
- Publish directory: `site`

---

## 5. Fluxo de trabalho (deploy)

Caminho local da pasta no PC do Renato (Windows):
```
C:\Users\renat\Downloads\economistarenato_site\economistarenato
```

Para publicar qualquer alteração:
```bash
git add .
git commit -m "descrição da mudança"
git push
```
O Netlify detecta o push e republica automaticamente em ~1 minuto.

Forçar redeploy sem mudança de arquivo:
```bash
git commit --allow-empty -m "Forcar novo deploy"
git push
```

> Autenticação do GitHub usa **token** (não senha) via Git Credential Manager.

---

## 6. Pendências conhecidas / o que ainda falta

1. **Confirmar domínio no ar** — houve histórico de o domínio apontar para um site
   antigo ("Renato Gomes" de projeto anterior) em vez do repositório correto.
   Verificar se `economistarenato.com.br` hoje serve o conteúdo de
   `site/index.html`. Checar status "verde" em Netlify → Domain settings, e se o
   A record `75.2.60.5` está salvo corretamente no Registro.br.
2. **E-mail profissional** — desejado `renato@economistarenato.com.br`. Ainda não
   configurado (na última conversa). Opções avaliadas: Zoho Mail (grátis, 1 usuário,
   recomendado), Google Workspace (~R$35/mês), Cloudflare Email Routing (grátis,
   só redireciona). Requer adicionar registros MX no Registro.br.
3. **Script de coleta SICONFI/RREO** — ficou em aberto se seria implementado.

---

## 7. Convenções de conteúdo (importante para gerar texto do site)

- **Tom:** economista institucional, sóbrio, técnico. Nunca populista.
- **Toda afirmação numérica precisa de fonte primária citada** (órgão + base/ano).
- **Fontes preferidas:** Portal da Transparência MS, LOA, Diário Oficial, SICONFI/RREO,
  IBGE, MDIC/ComexStat, SEMAGRO.
- **Posicionamento político:** oposição ao eixo Azambuja–Riedel, fundamentado em
  dados de governança pública (e não em ataque pessoal).
- **Base doutrinária do autor:** Doutrina Social da Igreja; relevante para o
  enquadramento de propostas, não para o site de dados em si.
- **Cuidado eleitoral:** o autor é pré-candidato. Conteúdo deve respeitar as regras
  de pré-campanha (Art. 36-A da Lei 9.504/97). Evitar pedido explícito de voto e
  propaganda eleitoral antecipada. Em dúvida sobre uma peça específica, sinalizar.

---

## 8. Como pedir ajuda ao Claude Code neste projeto

Exemplos de tarefas típicas:
- "Atualize os indicadores em `dados/indicadores.json` com os números de [fonte]."
- "Adicione uma nova seção de análise no `site/index.html` sobre [tema]."
- "Faça commit e push das mudanças."
- "Verifique se o site está apontando para o repositório correto no Netlify."
- "Implemente o `scripts/atualiza_dados.py` para coletar dados do SICONFI."

> Regra de segurança: **não** insira tokens, senhas ou credenciais em nenhum arquivo
> versionado. Use o gerenciador de credenciais do Git / variáveis de ambiente.
