# economistarenato.com.br

Site de análises técnicas de economia e finanças públicas do MS.

## Estrutura

```
economistarenato/
├── dados/
│   └── indicadores.json     ← VOCÊ EDITA ESTE ARQUIVO
├── scripts/
│   └── atualiza_dados.py    ← Script Python de coleta automática
├── site/
│   └── index.html           ← Site completo
├── netlify.toml             ← Configuração de hospedagem
└── README.md
```

## Como atualizar os dados

### Opção 1 — Manual (mais simples)
Edite o arquivo `dados/indicadores.json` diretamente com os novos valores, depois:
```bash
git add dados/indicadores.json
git commit -m "Atualiza indicadores - abr/2025"
git push
```
O site atualiza automaticamente em ~1 minuto.

### Opção 2 — Script Python automático
```bash
python scripts/atualiza_dados.py
git add dados/indicadores.json
git commit -m "Dados atualizados automaticamente"
git push
```

## Publicação inicial

1. Crie conta em https://github.com e https://netlify.com
2. Crie repositório no GitHub: `economistarenato`
3. Faça upload desta pasta ou use:
   ```bash
   git init
   git add .
   git commit -m "Primeiro deploy"
   git branch -M main
   git remote add origin https://github.com/SEU_USUARIO/economistarenato.git
   git push -u origin main
   ```
4. No Netlify: "Add new site" → "Import from Git" → selecione o repositório
5. Configure o domínio: "Domain settings" → adicione `economistarenato.com.br`
6. No Registro.br, aponte os nameservers para o Netlify (ele fornece)

## Domínio

Registre em: https://registro.br
- Domínio: `economistarenato.com.br`
- Custo: ~R$ 40/ano
- Renovação anual automática disponível
