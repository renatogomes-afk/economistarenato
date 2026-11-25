(function () {
  const D = window.DEMO;
  const brl = v => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  const dt = s => { const [, m, d] = s.split('-'); return `${d}/${m}`; };
  const today = new Date(); today.setHours(0,0,0,0);
  const iso = x => x.toISOString().slice(0,10);
  const addDays = n => { const x = new Date(today); x.setDate(x.getDate() + n); return iso(x); };
  const diasAte = s => Math.round((new Date(s + 'T00:00:00') - today) / 864e5);
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const pj = D.saldos.filter(s => s.tipo === 'PJ').reduce((a, s) => a + s.saldo, 0);
  const pf = D.saldos.filter(s => s.tipo === 'PF').reduce((a, s) => a + s.saldo, 0);
  let importadas = [];
  const pagarTodas = () => D.pagar.concat(importadas);
  const abertas = () => pagarTodas().filter(p => p.status !== 'pago');

  // ---- certidões e regra órgão → documentos ----
  const cert = nome => D.certidoes.find(c => c.nome === nome);
  function situacao(nome) {
    const c = cert(nome);
    if (!c) return { cls: 'classificar', txt: 'falta' };
    if (!c.validade) return { cls: 'enviado', txt: 'ok' };
    const n = diasAte(c.validade);
    if (n < 0) return { cls: 'classificar', txt: `vencida há ${-n} d` };
    if (n <= 15) return { cls: 'pendente', txt: `vence em ${n} d` };
    return { cls: 'enviado', txt: `válida até ${dt(c.validade)}` };
  }
  const registros = new Set(D.orgaos.map(o => o.registro));
  const orgaoDe = nome => D.orgaos.find(x => x.nome === nome);
  // Órgão mapeado: só o que ele exige. Não mapeado (ou "enviar tudo"): todas as certidões, mais o registro desse órgão.
  const exigidos = (orgao, tudo) => {
    const o = orgaoDe(orgao);
    if (!o || tudo || !o.mapeado) return D.certidoes.filter(c => !registros.has(c.nome)).map(c => c.nome).concat(o ? [o.registro] : []);
    return D.padrao.concat(o.extras, [o.registro]);
  };
  const piPronta = pi => exigidos(pi.orgao).every(n => situacao(n).cls !== 'classificar');
  const assunto = pi => `Processo - PI ${pi.numero} ${pi.orgao}`;
  const corpo = pi => `Segue anexo os documentos referentes ao processo da PI ${pi.numero} da ${pi.orgao}.\n\nAtt\nRoger`;

  // ---- fluxo de caixa (conta PJ) ----
  function fluxo(dias) {
    const pts = []; let s = pj;
    for (let i = 0; i <= dias; i++) {
      const day = addDays(i);
      abertas().filter(p => p.venc === day).forEach(p => s -= p.valor);
      D.receber.filter(r => r.venc === day).forEach(r => s += r.valor);
      pts.push({ day, s });
    }
    return pts;
  }
  function chart(pts) {
    const W = 720, H = 220, L = 56, R = 16, T = 16, B = 30;
    const vals = pts.map(p => p.s), lo = Math.min(0, ...vals), hi = Math.max(...vals) * 1.05;
    const X = i => L + i * (W - L - R) / (pts.length - 1), Y = v => T + (hi - v) * (H - T - B) / (hi - lo);
    const ticks = [0, 0.5, 1].map(f => lo + f * (hi - lo));
    const path = pts.map((p, i) => `${i ? 'L' : 'M'}${X(i).toFixed(1)} ${Y(p.s).toFixed(1)}`).join('');
    return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Fluxo de caixa projetado 30 dias">
      ${ticks.map(t => `<line x1="${L}" x2="${W - R}" y1="${Y(t)}" y2="${Y(t)}" stroke="var(--line)"/><text x="${L - 8}" y="${Y(t) + 4}" text-anchor="end" font-size="13" fill="var(--muted)">${Math.round(t / 1000)} mil</text>`).join('')}
      ${[0, 10, 20, 30].map(i => `<text x="${X(i)}" y="${H - 8}" text-anchor="middle" font-size="13" fill="var(--muted)">${dt(pts[i].day)}</text>`).join('')}
      <path d="${path}" fill="none" stroke="var(--brand)" stroke-width="3"/></svg>`;
  }

  // ---- importação do grupo de WhatsApp (sem IA: padrões de texto) ----
  function parseWhats(txt) {
    const out = [];
    txt.split(/\r?\n/).forEach(l => {
      const m = l.match(/^\[?(\d{2})\/(\d{2})\/(\d{2,4})[ ,]+\d{1,2}:\d{2}(?::\d{2})?\]?\s*-?\s*[^:]+:\s*(.+)$/);
      if (!m) return;
      const msg = m[4], ano = m[3].length === 2 ? '20' + m[3] : m[3];
      const v = msg.match(/(?:R\$\s*)?(\d{1,3}(?:\.\d{3})*(?:,\d{2})|\d+(?:,\d{2})?)(?!\/)/);
      if (!v) return;
      const valor = parseFloat(v[1].replace(/\./g, '').replace(',', '.'));
      let venc = null, dm = msg.match(/(\d{1,2})\/(\d{1,2})(?:\/(\d{2,4}))?/), dd = msg.match(/dia\s+(\d{1,2})/i);
      const base = new Date(`${ano}-${m[2]}-${m[1]}T00:00:00`);
      if (dm) { const a = dm[3] ? (dm[3].length === 2 ? '20' + dm[3] : dm[3]) : base.getFullYear(); venc = `${a}-${dm[2].padStart(2, '0')}-${dm[1].padStart(2, '0')}`; }
      else if (dd) { const x = new Date(base); x.setDate(+dd[1]); if (x < base) x.setMonth(x.getMonth() + 1); venc = iso(x); }
      const desc = msg.replace(v[0], '').replace(/R\$/g, '').replace(/(venc(imento)?|dia)\s+[\d\/]+/i, '').replace(/\d{1,2}\/\d{1,2}(\/\d{2,4})?/, '').replace(/\s+/g, ' ').trim();
      out.push({ desc: desc.charAt(0).toUpperCase() + desc.slice(1), fornecedor: '—', categoria: 'A classificar', venc: venc || iso(base), valor, origem: 'Grupo do WhatsApp', status: 'pendente', importada: true });
    });
    return out;
  }

  const views = {
    painel() {
      const p7 = abertas().filter(p => p.venc <= addDays(7)).reduce((a, p) => a + p.valor, 0);
      const pts = fluxo(30), min = pts.reduce((m, p) => p.s < m.s ? p : m, pts[0]);
      const alertas = D.certidoes.filter(c => c.validade && diasAte(c.validade) <= 15);
      const piPend = D.pis.filter(p => p.status !== 'enviada');
      return `<h1>Bom dia, Roger</h1><p class="sub">${dt(iso(today))} · saldos lidos por Open Finance</p>
      <div class="grid">
        <div class="card kpi"><div class="label">Saldo PJ (C6)</div><div class="value">${brl(pj)}</div></div>
        <div class="card kpi"><div class="label">A pagar em 7 dias</div><div class="value bad">${brl(p7)}</div></div>
        <div class="card kpi"><div class="label">Menor saldo em 30 dias</div><div class="value ${min.s < 0 ? 'bad' : ''}">${brl(min.s)}</div><div class="label">em ${dt(min.day)}</div></div>
        <div class="card kpi"><div class="label">Contas PF (C6, Mercado Pago, BB)</div><div class="value">${brl(pf)}</div></div>
      </div>
      ${alertas.length || piPend.length ? `<div class="card" style="margin-bottom:12px"><strong>Atenção hoje</strong><ul class="alerts">
        ${alertas.map(c => `<li><span class="tag ${situacao(c.nome).cls}">${situacao(c.nome).txt}</span> ${esc(c.nome)}</li>`).join('')}
        ${piPend.map(p => `<li><a href="#pis/${p.numero}">PI ${p.numero}</a> · ${esc(p.orgao)} ainda não enviada</li>`).join('')}</ul></div>` : ''}
      <div class="card chart"><strong>Fluxo de caixa PJ, 30 dias</strong><p class="muted" style="margin:4px 0 8px">Saldo de hoje menos contas a pagar, mais recebimentos previstos.</p>${chart(pts)}</div>
      <div class="card" style="margin-top:12px"><strong>Saldos por conta</strong><table>${D.saldos.map(s => `<tr><td>${esc(s.conta)}</td><td class="num">${brl(s.saldo)}</td></tr>`).join('')}</table></div>`;
    },
    pis(sel) {
      if (sel === 'nova') return views.novaPi();
      const pi = D.pis.find(p => p.numero === sel);
      if (pi) {
        const docs = exigidos(pi.orgao);
        const o = orgaoDe(pi.orgao);
        return `<p><a href="#pis">← PIs</a></p><h1>PI ${pi.numero}</h1><p class="sub">${esc(pi.orgao)} · ${esc(pi.cliente)}</p>
        <div class="card" style="margin-bottom:12px"><strong>${o && o.mapeado ? 'Documentos que este órgão exige' : 'Enviando tudo (exigências deste órgão ainda não mapeadas)'}</strong><ul class="alerts">
          ${docs.map(n => `<li><span class="tag ${situacao(n).cls}">${situacao(n).txt}</span> ${esc(n)}</li>`).join('')}</ul></div>
        <div class="card" style="margin-bottom:12px"><strong>E-mail preparado</strong>
          <pre class="mail">Para: ${esc(pi.para)}\nAssunto: ${esc(assunto(pi))}\n\n${esc(corpo(pi))}\n\nAnexos: ${docs.map(esc).join('; ')}</pre>
          ${piPronta(pi) ? '' : '<p class="bad">Há documento vencido ou faltando. Atualize antes de enviar.</p>'}
          <div class="btns"><button class="primary" disabled title="Desativado na demonstração">Enviar</button><button disabled>Editar</button></div></div>
        <div class="card"><strong>Pasta da PI</strong><ul class="alerts">
          <li>Nota fiscal: ${pi.pasta.nf ? esc(pi.pasta.nf) : '<span class="tag pendente">ainda não emitida</span>'}</li>
          <li>Prints de veiculação: ${pi.pasta.prints.map(esc).join(', ')}</li></ul></div>`;
      }
      return `<div class="head"><div><h1>PIs</h1><p class="sub">Cada pedido de inserção vira uma pasta com documentos, NF e prints, e um e-mail pronto.</p></div><a class="btn primary" href="#pis/nova">+ Nova PI</a></div>
      ${D.pis.map(p => `<a class="card picard" href="#pis/${p.numero}"><div><strong>PI ${p.numero}</strong> · ${esc(p.orgao)}<div class="muted">${esc(p.cliente)} · ${dt(p.data)}</div></div>
        <span class="tag ${p.status === 'enviada' ? 'enviado' : piPronta(p) ? 'pendente' : 'classificar'}">${p.status === 'enviada' ? 'enviada' : piPronta(p) ? 'pronta p/ enviar' : 'falta documento'}</span></a>`).join('')}`;
    },
    novaPi() {
      return `<p><a href="#pis">← PIs</a></p><h1>Nova PI</h1><p class="sub">Escolha o órgão e a plataforma junta os documentos certos e monta o e-mail.</p>
      <div class="card form"><label>Número da PI<input id="f-num" inputmode="numeric" placeholder="ex.: 10250"></label>
        <label>Órgão<select id="f-org">${D.orgaos.map(o => `<option>${esc(o.nome)}</option>`).join('')}</select></label>
        <label>Cliente (agência)<input id="f-cli" placeholder="ex.: Agência Exemplo Um"></label>
        <label>Enviar para<input id="f-para" type="email" placeholder="email@cliente"></label>
        <label class="check"><input id="f-tudo" type="checkbox"> Enviar todos os documentos, mesmo os que o órgão não exige</label></div>
      <div id="f-out"></div>`;
    },
    contas() {
      const rows = [...pagarTodas()].sort((a, b) => a.venc.localeCompare(b.venc)).map(p => `<tr>
        <td>${dt(p.venc)}</td><td><strong>${esc(p.desc)}</strong><div class="muted">${esc(p.origem)}${p.importada ? ' · importada agora' : ''}</div></td>
        <td class="num">${brl(p.valor)}</td></tr>`).join('');
      return `<h1>Contas a pagar</h1><p class="sub">Impostos, honorários, fornecedores e o que você anota no WhatsApp. A plataforma não paga: você paga no banco e a conciliação dá a baixa.</p>
      <div class="card" style="margin-bottom:12px"><strong>Importar do seu grupo do WhatsApp</strong>
        <p class="muted">No grupo: ⋮ › Mais › Exportar conversa › Sem mídia. Cole o texto aqui. Linhas com valor viram conta; o resto é ignorado.</p>
        <textarea id="wa" rows="5">${esc(D.whatsappExemplo)}</textarea>
        <div class="btns"><button class="primary" id="wa-go">Ler mensagens</button></div><div id="wa-out"></div></div>
      <div class="card"><table><thead><tr><th>Venc.</th><th>Conta</th><th class="num">Valor</th></tr></thead><tbody>${rows}</tbody></table></div>`;
    },
    documentos() {
      return `<h1>Documentos</h1><p class="sub">Certidões e registros com controle de validade, e a regra de quais documentos cada órgão exige.</p>
      <div class="card" style="margin-bottom:12px"><strong>Certidões e registros</strong><table>
        ${[...D.certidoes].sort((a, b) => (a.validade || '9').localeCompare(b.validade || '9')).map(c => `<tr><td>${esc(c.nome)}</td><td class="num"><span class="tag ${situacao(c.nome).cls}">${situacao(c.nome).txt}</span></td></tr>`).join('')}</table></div>
      <div class="card"><strong>O que cada órgão exige</strong><p class="muted">Base: ${D.padrao.map(esc).join(', ')}. Órgão ainda não mapeado recebe todos os documentos, como hoje.</p><table>
        <thead><tr><th>Órgão</th><th>Registro</th><th class="hide-sm">Exige também</th><th>Regra</th></tr></thead>
        ${D.orgaos.map(o => `<tr><td>${esc(o.nome)}</td><td>${esc(o.registro)}</td><td class="hide-sm">${o.mapeado ? (o.extras.map(esc).join(', ') || '—') : '—'}</td><td><span class="tag ${o.mapeado ? 'enviado' : 'pendente'}">${o.mapeado ? 'mapeado' : 'envia tudo'}</span></td></tr>`).join('')}</table></div>`;
    },
    resumo() {
      const p7 = abertas().filter(p => p.venc <= addDays(7)).sort((a, b) => a.venc.localeCompare(b.venc));
      const r7 = D.receber.filter(r => r.venc <= addDays(7));
      const pts = fluxo(30), min = pts.reduce((m, p) => p.s < m.s ? p : m, pts[0]);
      const alertas = D.certidoes.filter(c => c.validade && diasAte(c.validade) <= 15);
      const msg = `*FATO67 · Resumo de ${dt(iso(today))}*

Saldo PJ (C6): ${brl(pj)}
Contas PF: ${brl(pf)}

*A pagar nos próximos 7 dias*
${p7.map(p => `• ${dt(p.venc)} ${p.desc}: ${brl(p.valor)}`).join('\n')}

*A receber nos próximos 7 dias*
${r7.map(r => `• ${dt(r.venc)} ${r.ref}: ${brl(r.valor)}`).join('\n') || '• nada previsto'}

Menor saldo PJ em 30 dias: ${brl(min.s)} em ${dt(min.day)}

*Certidões*
${alertas.map(c => `• ${c.nome}: ${situacao(c.nome).txt}`).join('\n') || '• todas em dia'}

Abrir: economistarenato.com.br/fato67`;
      return `<h1>Resumo diário</h1><p class="sub">Chega todo dia às 7h no seu WhatsApp. Prévia de hoje:</p>
      <div class="phone"><div class="bubble">${esc(msg).replace(/\*(.+?)\*/g, '<strong>$1</strong>')}</div></div>`;
    }
  };

  function bind(route) {
    document.querySelectorAll('.tree li').forEach(li => li.addEventListener('click', () => { location.hash = 'documentos/' + encodeURIComponent(li.dataset.sel); }));
    const go = document.getElementById('wa-go');
    if (go) go.addEventListener('click', () => {
      const novas = parseWhats(document.getElementById('wa').value);
      importadas = novas;
      document.getElementById('wa-out').innerHTML = `<p class="good">${novas.length} contas encontradas e adicionadas abaixo.</p>`;
      const out = document.getElementById('app'); const keep = document.getElementById('wa').value;
      out.innerHTML = views.contas(); document.getElementById('wa').value = keep; bind('contas');
      document.getElementById('wa-out').innerHTML = `<p class="good">${novas.length} contas encontradas e adicionadas na lista.</p>`;
    });
    const num = document.getElementById('f-num');
    if (num) {
      const upd = () => {
        const pi = { numero: num.value || '_____', orgao: document.getElementById('f-org').value, cliente: document.getElementById('f-cli').value, para: document.getElementById('f-para').value || '—' };
        const o = orgaoDe(pi.orgao), tudo = document.getElementById('f-tudo').checked;
        const docs = exigidos(pi.orgao, tudo);
        document.getElementById('f-out').innerHTML = `<div class="card" style="margin-top:12px"><strong>Documentos que vão anexados (${docs.length})</strong>${o && !o.mapeado ? '<p class="muted">Este órgão ainda não tem regra; por segurança vai tudo.</p>' : ''}<ul class="alerts">
          ${docs.map(n => `<li><span class="tag ${situacao(n).cls}">${situacao(n).txt}</span> ${esc(n)}</li>`).join('')}</ul>
          <strong>E-mail</strong><pre class="mail">Para: ${esc(pi.para)}\nAssunto: ${esc(assunto(pi))}\n\n${esc(corpo(pi))}</pre>
          <div class="btns"><button class="primary" disabled title="Desativado na demonstração">Criar PI e enviar</button></div></div>`;
      };
      ['f-num', 'f-org', 'f-cli', 'f-para', 'f-tudo'].forEach(id => document.getElementById(id).addEventListener('input', upd)); document.getElementById('f-tudo').addEventListener('change', upd); upd();
    }
  }
  function render() {
    const [route, sel] = decodeURIComponent(location.hash.slice(1)).split('/');
    const r = views[route] && route !== 'novaPi' ? route : 'painel';
    document.getElementById('app').innerHTML = views[r](sel);
    document.querySelectorAll('nav a').forEach(a => a.classList.toggle('on', a.getAttribute('href') === '#' + r));
    bind(r); window.scrollTo(0, 0);
  }
  window.addEventListener('hashchange', render);
  render();
  if ('serviceWorker' in navigator && location.protocol === 'https:') navigator.serviceWorker.register('sw.js').catch(() => {});
})();
