(function () {
  const D = window.DEMO;
  const brl = v => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  const dt = s => { const [y, m, d] = s.split('-'); return `${d}/${m}`; };
  const today = new Date(); today.setHours(0,0,0,0);
  const iso = x => x.toISOString().slice(0,10);
  const addDays = n => { const x = new Date(today); x.setDate(x.getDate() + n); return iso(x); };
  const cli = id => (D.clientes.find(c => c.id === id) || {}).nome || 'FATO67 (interno)';
  const saldoTotal = D.saldos[0].saldo; // fluxo considera só a conta PJ
  const abertas = D.pagar.filter(p => p.status !== 'pago');
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  function fluxo(dias) {
    const pts = []; let s = saldoTotal;
    for (let i = 0; i <= dias; i++) {
      const day = addDays(i);
      abertas.filter(p => p.venc === day).forEach(p => s -= p.valor);
      D.receber.filter(r => r.venc === day).forEach(r => s += r.valor);
      pts.push({ day, s });
    }
    return pts;
  }

  function chart(pts) {
    const W = 720, H = 220, L = 70, R = 16, T = 16, B = 30;
    const vals = pts.map(p => p.s), lo = Math.min(0, ...vals), hi = Math.max(...vals) * 1.05;
    const X = i => L + i * (W - L - R) / (pts.length - 1), Y = v => T + (hi - v) * (H - T - B) / (hi - lo);
    const ticks = [0, 0.25, 0.5, 0.75, 1].map(f => lo + f * (hi - lo));
    const path = pts.map((p, i) => `${i ? 'L' : 'M'}${X(i).toFixed(1)} ${Y(p.s).toFixed(1)}`).join('');
    return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Fluxo de caixa projetado 30 dias">
      ${ticks.map(t => `<line x1="${L}" x2="${W - R}" y1="${Y(t)}" y2="${Y(t)}" stroke="var(--line)"/><text x="${L - 8}" y="${Y(t) + 4}" text-anchor="end" font-size="11" fill="var(--muted)">${Math.round(t / 1000)} mil</text>`).join('')}
      ${[0, 7, 14, 21, 30].map(i => `<text x="${X(i)}" y="${H - 8}" text-anchor="middle" font-size="11" fill="var(--muted)">${dt(pts[i].day)}</text>`).join('')}
      <path d="${path}" fill="none" stroke="var(--brand)" stroke-width="2.5"/>
    </svg>`;
  }

  const views = {
    painel() {
      const p7 = abertas.filter(p => p.venc <= addDays(7)).reduce((a, p) => a + p.valor, 0);
      const r30 = D.receber.reduce((a, r) => a + r.valor, 0);
      const pts = fluxo(30), min = pts.reduce((m, p) => p.s < m.s ? p : m, pts[0]);
      const pend = D.documentos.filter(x => x.status !== 'enviado').length;
      return `<h1>Painel</h1><p class="sub">Situação de hoje, ${dt(iso(today))}. Saldo lido do extrato por Open Finance.</p>
      <div class="grid">
        <div class="card kpi"><div class="label">Saldo hoje (C6 PJ)</div><div class="value">${brl(saldoTotal)}</div></div>
        <div class="card kpi"><div class="label">A pagar em 7 dias</div><div class="value bad">${brl(p7)}</div></div>
        <div class="card kpi"><div class="label">A receber em 30 dias</div><div class="value good">${brl(r30)}</div></div>
        <div class="card kpi"><div class="label">Menor saldo previsto</div><div class="value ${min.s < 0 ? 'bad' : ''}">${brl(min.s)}</div><div class="label">em ${dt(min.day)}</div></div>
        <div class="card kpi"><div class="label">Documentos pendentes</div><div class="value warn">${pend}</div></div>
      </div>
      <div class="card chart"><strong>Fluxo de caixa projetado, 30 dias</strong><p class="muted" style="margin:4px 0 8px">Saldo de hoje menos contas a pagar, mais recebimentos previstos.</p>${chart(pts)}</div>`;
    },
    pagar() {
      const rows = [...D.pagar].sort((a, b) => a.venc.localeCompare(b.venc)).map(p => `<tr>
        <td>${dt(p.venc)}</td><td><strong>${esc(p.desc)}</strong><div class="muted">${esc(p.fornecedor)}</div></td>
        <td class="hide-sm">${esc(p.categoria)}</td><td class="hide-sm muted">${esc(p.origem)}</td>
        <td class="num">${brl(p.valor)}</td><td><span class="tag ${p.status}">${p.status}</span></td></tr>`).join('');
      return `<h1>Contas a pagar</h1><p class="sub">Impostos, honorários, fornecedores e despesas. Lançadas sozinhas quando o documento é reconhecido. A plataforma não paga: o Roger paga no banco e a conciliação dá a baixa.</p>
      <div class="card"><table><thead><tr><th>Venc.</th><th>Conta</th><th class="hide-sm">Categoria</th><th class="hide-sm">Origem</th><th class="num">Valor</th><th>Status</th></tr></thead><tbody>${rows}</tbody></table></div>`;
    },
    documentos(sel) {
      const [c, s] = (sel || '').split('|');
      const list = D.documentos.filter(x => c === 'interno' ? !x.cliente : c ? x.cliente === c && (!s || x.servico === s) : true);
      const tree = `<ul class="tree">
        <li data-sel="" class="${!c ? 'on' : ''}">Todos os documentos</li>
        ${D.clientes.map(k => `<li data-sel="${k.id}" class="${c === k.id && !s ? 'on' : ''}">${esc(k.nome)}</li>
          ${k.servicos.map(v => `<li data-sel="${k.id}|${esc(v)}" class="svc ${c === k.id && s === v ? 'on' : ''}">${esc(v)}</li>`).join('')}`).join('')}
        <li data-sel="interno" class="${c === 'interno' ? 'on' : ''}">FATO67 interno (guias, honorários)</li></ul>`;
      const rows = list.map(x => `<tr><td>${dt(x.data)}</td><td><strong>${esc(x.tipo)}</strong><div class="muted">${esc(x.arquivo)}</div></td>
        <td class="hide-sm">${esc(cli(x.cliente))}${x.servico ? `<div class="muted">${esc(x.servico)}</div>` : ''}</td>
        <td class="hide-sm muted">${esc(x.regra)}</td><td><span class="tag ${x.status}">${x.status === 'classificar' ? 'a classificar' : x.status}</span></td></tr>`).join('');
      return `<h1>Documentos</h1><p class="sub">Arquivos organizados por cliente e por serviço executado. Reconhecidos por regras, sem IA; o que nenhuma regra reconhece fica "a classificar".</p>
      <div class="row"><div class="card" style="flex:0 1 280px">${tree}</div>
      <div class="card"><table><thead><tr><th>Data</th><th>Documento</th><th class="hide-sm">Cliente / serviço</th><th class="hide-sm">Como foi reconhecido</th><th>Status</th></tr></thead><tbody>${rows || '<tr><td colspan="5" class="muted">Nenhum documento.</td></tr>'}</tbody></table></div></div>`;
    },
    emails() {
      const docs = D.documentos.filter(x => x.cliente);
      const pend = docs.filter(x => x.status === 'pendente');
      const draft = x => `Para: financeiro@${x.cliente}.exemplo.com.br
Assunto: ${x.tipo} · ${x.servico}

Olá, equipe ${cli(x.cliente)},

Segue em anexo ${x.tipo.toLowerCase()} referente ao serviço "${x.servico}".
Qualquer dúvida, estou à disposição.

Atenciosamente,
Roger · FATO67

Anexo: ${x.arquivo}`;
      return `<h1>E-mails preparados</h1><p class="sub">Montados a partir dos documentos e de modelos por tipo. O Roger revisa e envia.</p>
      ${pend.map(x => `<div class="card" style="margin-bottom:12px"><div style="display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap"><strong>${esc(cli(x.cliente))} · ${esc(x.servico)}</strong><span class="tag pendente">aguardando revisão</span></div>
        <pre class="mail">${esc(draft(x))}</pre><div style="display:flex;gap:8px"><button class="primary" disabled title="Desativado na demonstração">Enviar</button><button disabled>Editar</button></div></div>`).join('')}`;
    },
    resumo() {
      const p7 = abertas.filter(p => p.venc <= addDays(7)).sort((a, b) => a.venc.localeCompare(b.venc));
      const r7 = D.receber.filter(r => r.venc <= addDays(7));
      const pts = fluxo(30), min = pts.reduce((m, p) => p.s < m.s ? p : m, pts[0]);
      const pend = D.documentos.filter(x => x.status !== 'enviado').length;
      const msg = `*FATO67 · Resumo de ${dt(iso(today))}*

Saldo hoje (C6 PJ): ${brl(saldoTotal)}

*A pagar nos próximos 7 dias*
${p7.map(p => `• ${dt(p.venc)} ${p.desc}: ${brl(p.valor)}`).join('\n')}

*A receber nos próximos 7 dias*
${r7.map(r => `• ${dt(r.venc)} ${cli(r.cliente)}: ${brl(r.valor)}`).join('\n') || '• nada previsto'}

Saldo projetado em 30 dias: ${brl(pts[30].s)}
Menor saldo previsto: ${brl(min.s)} em ${dt(min.day)}

${pend} documentos aguardando você.
Abrir o painel: economistarenato.com.br/fato67`;
      return `<h1>Resumo diário</h1><p class="sub">Mensagem enviada ao Roger todo dia às 7h, por WhatsApp ou e-mail. Prévia de hoje:</p>
      <div class="phone"><div class="bubble">${esc(msg).replace(/\*(.+?)\*/g, '<strong>$1</strong>')}</div></div>`;
    }
  };

  function render() {
    const [route, sel] = decodeURIComponent(location.hash.slice(1)).split('/');
    const r = views[route] ? route : 'painel';
    document.getElementById('app').innerHTML = views[r](sel);
    document.querySelectorAll('#nav a').forEach(a => a.classList.toggle('on', a.getAttribute('href') === '#' + r));
    document.querySelectorAll('.tree li').forEach(li => li.addEventListener('click', () => { location.hash = 'documentos/' + encodeURIComponent(li.dataset.sel); }));
  }
  window.addEventListener('hashchange', render);
  render();
  if ('serviceWorker' in navigator && location.protocol === 'https:') navigator.serviceWorker.register('sw.js').catch(() => {});
})();
