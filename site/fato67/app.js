(function () {
  // Dois modos: demonstração (sem login, dados fictícios de data.js) e real (logado, dados do Supabase via nuvem.js)
  let D = window.DEMO;
  const N = window.Nuvem;
  const real = () => !!D.real;
  const brl = v => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  const dt = s => { const [, m, d] = s.split('-'); return `${d}/${m}`; };
  const today = new Date(); today.setHours(0,0,0,0);
  const iso = x => `${x.getFullYear()}-${String(x.getMonth() + 1).padStart(2, '0')}-${String(x.getDate()).padStart(2, '0')}`;
  const addDays = n => { const x = new Date(today); x.setDate(x.getDate() + n); return iso(x); };
  const diasAte = s => Math.round((new Date(s + 'T00:00:00') - today) / 864e5);
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const pjF = () => D.saldos.filter(s => s.tipo === 'PJ').reduce((a, s) => a + s.saldo, 0);
  const pfF = () => D.saldos.filter(s => s.tipo === 'PF').reduce((a, s) => a + s.saldo, 0);
  const primeiro = () => { const u = D.usuario, m = (u && u.user_metadata) || {}; const n = u && (m.full_name || m.name || u.email); return n ? String(n).split(/[\s@]/)[0] : 'Roger'; };
  const saudacao = () => { const h = new Date().getHours(); return h < 12 ? 'Bom dia' : h < 18 ? 'Boa tarde' : 'Boa noite'; };
  let importadas = [];
  const pagarTodas = () => D.pagar.concat(importadas);
  const abertas = () => pagarTodas().filter(p => p.status !== 'pago');
  const avisar = (txt, cls = 'good') => { const t = document.getElementById('toast'); t.className = 'toast ' + cls; t.textContent = txt; t.hidden = false; clearTimeout(avisar.t); avisar.t = setTimeout(() => { t.hidden = true; }, 4500); };

  // ---- certidões e regra órgão → documentos ----
  const cert = nome => D.certidoes.find(c => c.nome === nome);
  function sitData(validade) {
    if (!validade) return { cls: 'enviado', txt: 'ok' };
    const n = diasAte(validade);
    if (n < 0) return { cls: 'classificar', txt: `vencida há ${-n} d` };
    if (n <= 15) return { cls: 'pendente', txt: `vence em ${n} d` };
    return { cls: 'enviado', txt: `válida até ${dt(validade)}` };
  }
  const vencidasInternas = c => (c.internas || []).filter(i => i.validade && diasAte(i.validade) < 0);
  function situacao(nome) {
    const c = cert(nome);
    if (!c) return { cls: 'classificar', txt: 'falta' };
    if (c.validade && diasAte(c.validade) < 0) return { cls: 'classificar', txt: `vencida há ${-diasAte(c.validade)} d` };
    const venc = vencidasInternas(c);
    if (venc.length) return { cls: 'classificar', txt: `${venc.length} internas vencidas` };
    if (c.semArquivo) return { cls: 'pendente', txt: 'sem arquivo' };
    if (!c.validade) return { cls: 'enviado', txt: 'ok' };
    const n = diasAte(c.validade);
    if (n <= 15) return { cls: 'pendente', txt: `vence em ${n} d` };
    return { cls: 'enviado', txt: `válida até ${dt(c.validade)}` };
  }
  const orgaoDe = nome => D.orgaos.find(x => x.nome === nome);
  // Órgão mapeado: só o que ele exige. Não mapeado (ou "enviar tudo"): todas as certidões, mais o registro desse órgão.
  const exigidos = (orgao, tudo) => {
    const o = orgaoDe(orgao), registros = new Set(D.orgaos.map(x => x.registro));
    if (!o || tudo || !o.mapeado) return D.certidoes.filter(c => !registros.has(c.nome)).map(c => c.nome).concat(o && o.registro ? [o.registro] : []);
    return D.padrao.concat(o.extras, o.registro ? [o.registro] : []);
  };
  // Agência + cliente → destinatário (atendente, senão e-mail padrão) e passos do processo
  const agenciaDe = n => D.agencias.find(a => a.nome === n);
  function destino(agencia, orgao) {
    const a = agenciaDe(agencia); if (!a) return { email: '', txt: 'agência sem cadastro' };
    const at = a.atendentes.find(x => x.cliente === orgao);
    return at ? { email: at.email, txt: `${at.nome}, atendente de ${orgao}` }
      : { email: a.padrao, txt: a.padrao ? 'e-mail padrão da agência (sem atendente para este cliente)' : 'agência ainda sem e-mail cadastrado' };
  }
  const manualDe = (agencia, orgao) => D.manuais.find(m => m.agencia === agencia && m.cliente === orgao);
  const passos = (agencia, orgao) => (manualDe(agencia, orgao) || { passos: D.passosPadrao }).passos;

  // Anexos da PI: começa pela regra do órgão; o Roger marca e desmarca
  const docsPi = pi => (pi.sel = pi.sel || exigidos(pi.orgao).concat(pi.avulsos || []));
  const piPronta = pi => docsPi(pi).every(n => situacao(n).cls !== 'classificar' || (pi.avulsos || []).includes(n));
  const assunto = pi => `Processo - PI ${pi.numero} ${pi.orgao}`;
  const corpo = pi => `Segue anexo os documentos referentes ao processo da PI ${pi.numero} (${pi.orgao}).\n\nAtt\nRoger Usai`;
  const piAtual = () => D.pis.find(p => p.numero === decodeURIComponent(location.hash).split('/')[1]);

  // ---- fluxo de caixa (conta PJ) ----
  function fluxo(dias) {
    const pts = []; let s = pjF();
    for (let i = 0; i <= dias; i++) {
      const day = addDays(i);
      // contas vencidas e não pagas entram no primeiro dia
      abertas().filter(p => (i === 0 ? p.venc <= day : p.venc === day)).forEach(p => s -= p.valor);
      D.receber.filter(r => (i === 0 ? r.venc <= day : r.venc === day)).forEach(r => s += r.valor);
      pts.push({ day, s });
    }
    return pts;
  }
  function chart(pts) {
    const W = 720, H = 220, L = 56, R = 16, T = 16, B = 30;
    const vals = pts.map(p => p.s), lo = Math.min(0, ...vals), hi = Math.max(1000, ...vals) * 1.05;
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

  // ---- pasta da PI: ZIP e PDF único ----
  const nomeArq = n => n.normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^\w]+/g, '_');
  const arquivosPi = pi => docsPi(pi).map((n, i) => `${String(i + 1).padStart(2, '0')}_${nomeArq(n)}.pdf`)
    .concat(pi.pasta.nf ? [pi.pasta.nf] : [], pi.pasta.prints.map(p => 'prints/' + p));
  async function baixarZip(pi) {
    if (!window.JSZip) { return; }
    const zip = new JSZip(), pasta = zip.folder(`PI_${pi.numero}`);
    pasta.file('00_email.txt', `Para: ${destino(pi.cliente, pi.orgao).email}\nAssunto: ${assunto(pi)}\n\n${corpo(pi)}\n`);
    if (real()) {
      const faltam = [], arqs = pi.pasta.arquivos || [];
      const ext = c => (c.match(/\.\w+$/) || ['.pdf'])[0];
      await Promise.all(docsPi(pi).map(async (n, i) => {
        const c = cert(n) || arqs.find(a => a.tipo === 'avulso' && a.nome === n);
        if (!c || !c.arquivo) { faltam.push(n); return; }
        pasta.file(`${String(i + 1).padStart(2, '0')}_${nomeArq(n.replace(/\.\w+$/, ''))}${ext(c.arquivo)}`, await N.baixar(c.arquivo));
      }));
      await Promise.all(arqs.filter(a => a.tipo !== 'avulso').map(async a => pasta.file((a.tipo === 'print' ? 'prints/' : '') + a.nome, await N.baixar(a.arquivo))));
      pasta.file('00_indice.txt', `PI ${pi.numero} · ${pi.orgao} · ${pi.cliente}\n\n` + docsPi(pi).map(f => `- ${f}`).join('\n')
        + (faltam.length ? `\n\nSem arquivo guardado na plataforma (anexar à mão): ${faltam.join(', ')}\n` : '\n'));
    } else {
      pasta.file('00_indice.txt', `PI ${pi.numero} · ${pi.orgao} · ${pi.cliente}\n\n` + arquivosPi(pi).map(f => `- ${f}`).join('\n') + '\n\nDemonstração: os arquivos reais entram aqui na versão final.\n');
    }
    const blob = await zip.generateAsync({ type: 'blob' });
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `PI_${pi.numero}.zip`; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 5000);
  }
  function imprimir(pi) {
    const docs = docsPi(pi);
    const el = document.getElementById('print');
    el.innerHTML = `<section class="pg"><h1>Processo · PI ${esc(pi.numero)}</h1><p>${esc(pi.orgao)}<br>${esc(pi.cliente)}<br>${dt(iso(today))}</p>
      <h2>Índice</h2><ol>${docs.map(n => `<li>${esc(n)}</li>`).join('')}${pi.pasta.nf ? '<li>Nota fiscal</li>' : ''}<li>Comprovantes de veiculação (${pi.pasta.prints.length})</li></ol></section>
      ${docs.map(n => `<section class="pg"><h2>${esc(n)}</h2><p class="muted">${real() ? 'Anexe aqui o documento (no ZIP vão os arquivos guardados).' : 'Na versão final, aqui entram as páginas do documento.'}</p></section>`).join('')}`;
    window.print();
  }

  const views = {
    painel() {
      const p7 = abertas().filter(p => p.venc <= addDays(7)).reduce((a, p) => a + p.valor, 0);
      const pts = fluxo(30), min = pts.reduce((m, p) => p.s < m.s ? p : m, pts[0]);
      const alertas = D.certidoes.filter(c => c.validade && diasAte(c.validade) <= 15);
      const piPend = D.pis.filter(p => p.status !== 'enviada');
      const velhos = real() ? D.saldos.filter(s => s.data !== iso(today)) : [];
      return `<h1>${saudacao()}, ${esc(primeiro())}</h1><p class="sub">${dt(iso(today))} · ${real() ? esc(D.empresa.nome) + ' · saldos digitados ou lidos do extrato' : 'saldos lidos por Open Finance'}</p>
      ${velhos.length ? `<a class="card picard" href="#bancos" style="margin-bottom:12px"><div><strong>Atualizar os saldos de hoje</strong><div class="muted">${velhos.map(s => esc(s.conta)).join(', ')}</div></div><span class="tag pendente">${velhos.length}</span></a>` : ''}
      <div class="grid">
        <div class="card kpi"><div class="label">Saldo PJ (C6)</div><div class="value">${brl(pjF())}</div></div>
        <div class="card kpi"><div class="label">A pagar em 7 dias</div><div class="value bad">${brl(p7)}</div></div>
        <div class="card kpi"><div class="label">Menor saldo em 30 dias</div><div class="value ${min.s < 0 ? 'bad' : ''}">${brl(min.s)}</div><div class="label">em ${dt(min.day)}</div></div>
        <div class="card kpi"><div class="label">Contas PF (C6, Mercado Pago, BB)</div><div class="value">${brl(pfF())}</div></div>
      </div>
      ${alertas.length || piPend.length ? `<div class="card" style="margin-bottom:12px"><strong>Atenção hoje</strong><ul class="alerts">
        ${alertas.map(c => `<li><span class="tag ${situacao(c.nome).cls}">${situacao(c.nome).txt}</span> ${esc(c.nome)}</li>`).join('')}
        ${piPend.map(p => `<li><a href="#pis/${encodeURIComponent(p.numero)}">PI ${esc(p.numero)}</a> · ${esc(p.orgao)} ainda não enviada</li>`).join('')}</ul></div>` : ''}
      ${D.entrada.filter(e => !e.feito).length ? `<div class="card" style="margin-bottom:12px"><strong>Chegou por e-mail</strong><p class="muted">Anexos reconhecidos pelas regras. Confirme para guardar.</p><ul class="alerts">
        ${D.entrada.map((e, i) => `<li>${e.feito ? `<span class="tag enviado">guardado</span> ${esc(e.arquivo)}` : `<strong>${esc(e.arquivo)}</strong><div class="muted">de ${esc(e.de)} · parece: ${esc(e.parece)}</div><div class="btns"><button class="primary" data-in="${i}">Confirmar</button><button data-in-x="${i}">Não é isso</button></div>`}</li>`).join('')}</ul></div>` : ''}
      <div class="card chart"><strong>Fluxo de caixa PJ, 30 dias</strong><p class="muted" style="margin:4px 0 8px">Saldo de hoje menos contas a pagar, mais recebimentos previstos.</p>${chart(pts)}</div>
      <div class="card" style="margin-top:12px"><strong>Saldos por conta</strong><table>${D.saldos.map(s => `<tr><td>${esc(s.conta)}${real() ? `<div class="muted">${s.data ? 'em ' + dt(s.data) : 'saldo ainda não informado'}</div>` : ''}</td><td class="num">${brl(s.saldo)}</td></tr>`).join('')}</table>
        ${real() ? '<div class="btns"><a class="btn" href="#bancos">Informar saldo ou importar extrato</a></div>' : ''}</div>`;
    },
    bancos() {
      const contas = D.saldos;
      const ext = D.extrato || [];
      return `<h1>Bancos</h1><p class="sub">Enquanto o Open Finance não entra, o saldo vem de duas formas: você digita o saldo do dia, ou importa o extrato (OFX ou CSV) baixado no app do banco.</p>
      ${real() ? '' : '<p class="bad">Demonstração: entre com sua conta para guardar saldos e extratos.</p>'}
      <div class="card form" style="margin-bottom:12px"><strong>Saldo de hoje</strong><p class="muted">Abra o app do banco, veja o saldo e digite aqui. Leva um minuto.</p>
        ${contas.map(s => `<label>${esc(s.conta)} <span class="muted">${s.data ? `· último: ${brl(s.saldo)} em ${dt(s.data)}` : ''}</span><input inputmode="decimal" data-saldo="${esc(s.id || s.conta)}" placeholder="ex.: 12.345,67"></label>`).join('')}
        <div class="btns"><button class="primary" id="saldo-ok" ${real() ? '' : 'disabled'}>Guardar saldos</button></div></div>
      <div class="card form" style="margin-bottom:12px"><strong>Importar extrato</strong>
        <p class="muted">C6 e Banco do Brasil: extrato › exportar › OFX. Mercado Pago: Seu dinheiro › Relatórios › CSV. Importar de novo o mesmo período não duplica.</p>
        <label>Conta<select id="ex-conta">${contas.map(s => `<option value="${esc(s.id || '')}">${esc(s.conta)}</option>`).join('')}</select></label>
        <label>Arquivo (.ofx ou .csv)<input type="file" id="ex-file" accept=".ofx,.csv,.txt,text/csv,application/x-ofx"></label>
        <div id="ex-out"></div></div>
      <div class="card"><strong>Últimos lançamentos</strong>${ext.length ? `<table>${ext.slice(0, 40).map(x => `<tr><td>${dt(x.data)}</td><td>${esc(x.descricao)}<div class="muted">${esc((contas.find(c => c.id === x.conta_id) || {}).conta)}</div></td><td class="num ${x.valor < 0 ? 'bad' : 'good'}">${brl(x.valor)}</td></tr>`).join('')}</table>` : '<p class="muted">Nenhum extrato importado ainda.</p>'}</div>`;
    },
    pis(sel) {
      if (sel === 'nova') return views.novaPi();
      const pi = D.pis.find(p => p.numero === sel);
      if (pi) {
        const docs = docsPi(pi), regra = exigidos(pi.orgao);
        const o = orgaoDe(pi.orgao);
        const outros = D.certidoes.map(c => c.nome).filter(n => !docs.includes(n));
        const linha = (n, on) => `<li><label class="pick"><input type="checkbox" data-doc="${esc(n)}" ${on ? 'checked' : ''}>
          <span>${esc(n)}${regra.includes(n) || (pi.avulsos || []).includes(n) ? '' : ' <span class="muted">(fora da regra)</span>'}${on && cert(n) && vencidasInternas(cert(n)).length ? `<div class="muted">Atualizar e anexar: ${vencidasInternas(cert(n)).map(i => esc(i.nome)).join(', ')}</div>` : ''}</span>
          ${cert(n) ? `<span class="tag ${situacao(n).cls}">${situacao(n).txt}</span>` : '<span class="tag">avulso</span>'}</label></li>`;
        const dst = destino(pi.cliente, pi.orgao);
        return `<p><a href="#pis">← PIs</a></p><h1>PI ${esc(pi.numero)}</h1><p class="sub">${esc(pi.orgao)} · ${esc(pi.cliente)}</p>
        <div class="card" style="margin-bottom:12px"><strong>Anexos (${docs.length})</strong>
          <p class="muted">${o && o.mapeado ? 'Marcados pela regra do órgão.' : 'Órgão sem regra: tudo marcado.'} Toque para tirar ou incluir.</p>
          <ul class="alerts">${docs.map(n => linha(n, true)).join('')}</ul>
          ${outros.length ? `<details><summary>Incluir outro documento da biblioteca (${outros.length})</summary><ul class="alerts">${outros.map(n => linha(n, false)).join('')}</ul></details>` : ''}
          <label class="btn up">+ Anexar arquivo só nesta PI<input type="file" class="pi-up" data-tipo="avulso" accept="application/pdf,image/*" hidden></label></div>
        <div class="card" style="margin-bottom:12px"><strong>E-mail preparado</strong>
          <p class="muted">Para: ${esc(dst.txt)}</p><pre class="mail">Para: ${esc(dst.email || '—')}\nAssunto: ${esc(assunto(pi))}\n\n${esc(corpo(pi))}\n\nAnexos: ${docs.map(esc).join('; ')}</pre>
          ${piPronta(pi) ? '' : '<p class="bad">Há documento vencido ou faltando. Atualize antes de enviar.</p>'}
          ${real() ? `<div class="btns"><a class="btn primary" href="mailto:${esc(dst.email)}?subject=${encodeURIComponent(assunto(pi))}&body=${encodeURIComponent(corpo(pi))}">Abrir no e-mail</a>${pi.status === 'enviada' ? '' : '<button id="pi-enviada">Marcar como enviada</button>'}</div><p class="muted">Baixe o ZIP abaixo e anexe no e-mail. O envio pela própria plataforma vem depois.</p>`
            : '<div class="btns"><button class="primary" disabled title="Desativado na demonstração">Enviar</button><button disabled>Editar</button></div>'}</div>
        <div class="card" style="margin-bottom:12px"><strong>Passos do processo</strong><p class="muted">${manualDe(pi.cliente, pi.orgao) ? `Do manual "${esc(pi.cliente)} + ${esc(pi.orgao)}".` : 'Passos padrão: ainda não há manual para esta combinação.'}</p>
          <ul class="alerts">${passos(pi.cliente, pi.orgao).map((t, i) => `<li><label class="pick"><input type="checkbox" data-passo="${i}" ${pi.status === 'enviada' || i < (pi.feitos || 0) ? 'checked' : ''}><span>${esc(t)}</span></label></li>`).join('')}</ul></div>
        <div class="card" style="margin-bottom:12px"><strong>Baixar a pasta da PI</strong><p class="muted">Para enviar ou imprimir o processo, como algumas agências pedem.</p>
          <div class="btns"><button class="primary" id="dl-zip">Baixar ZIP</button><button id="dl-pdf">PDF para imprimir</button></div></div>
        <div class="card"><strong>Pasta da PI</strong><ul class="alerts">
          <li>Nota fiscal: ${pi.pasta.nf ? esc(pi.pasta.nf) : '<span class="tag pendente">ainda não emitida</span>'}</li>
          <li>Prints de veiculação: ${pi.pasta.prints.map(esc).join(', ') || '—'}</li></ul>
          ${real() ? `<div class="btns"><label class="btn up">+ NF<input type="file" class="pi-up" data-tipo="nf" accept="application/pdf,image/*" hidden></label><label class="btn up">+ Prints<input type="file" class="pi-up" data-tipo="print" accept="image/*,application/pdf" multiple hidden></label></div>` : ''}</div>`;
      }
      return `<div class="head"><div><h1>PIs</h1><p class="sub">Cada pedido de inserção vira uma pasta com documentos, NF e prints, e um e-mail pronto.</p></div><a class="btn primary" href="#pis/nova">+ Nova PI</a></div>
      ${D.pis.length ? '' : '<p class="muted">Nenhuma PI cadastrada ainda.</p>'}
      ${D.pis.map(p => `<a class="card picard" href="#pis/${encodeURIComponent(p.numero)}"><div><strong>PI ${esc(p.numero)}</strong> · ${esc(p.orgao)}<div class="muted">${esc(p.cliente)} · ${dt(p.data)}</div></div>
        <span class="tag ${p.status === 'enviada' ? 'enviado' : piPronta(p) ? 'pendente' : 'classificar'}">${p.status === 'enviada' ? 'enviada' : piPronta(p) ? 'pronta p/ enviar' : 'falta documento'}</span></a>`).join('')}`;
    },
    novaPi() {
      return `<p><a href="#pis">← PIs</a></p><h1>Nova PI</h1><p class="sub">Escolha o órgão e a plataforma junta os documentos certos e monta o e-mail.</p>
      <div class="card form"><label>Número da PI<input id="f-num" inputmode="numeric" placeholder="ex.: 10250"></label>
        <label>Cliente final (órgão)<select id="f-org">${D.orgaos.map(o => `<option>${esc(o.nome)}</option>`).join('')}</select></label>
        <label>Agência<select id="f-cli">${D.agencias.map(a => `<option>${esc(a.nome)}</option>`).join('')}</select></label>
        <label class="check"><input id="f-tudo" type="checkbox"> Enviar todos os documentos, mesmo os que o órgão não exige</label></div>
      <div id="f-out"></div>`;
    },
    contas() {
      const rows = [...pagarTodas()].filter(p => p.status !== 'pago').sort((a, b) => a.venc.localeCompare(b.venc)).map(p => `<tr>
        <td>${dt(p.venc)}${diasAte(p.venc) < 0 ? '<div class="bad">vencida</div>' : ''}</td><td><strong>${esc(p.desc)}</strong><div class="muted">${esc(p.origem)}${p.importada ? ' · importada agora' : ''}</div></td>
        <td class="num">${brl(p.valor)}${real() && p.id ? `<div><button class="link" data-paga="${p.id}">paguei</button></div>` : ''}</td></tr>`).join('');
      const rec = [...D.receber].sort((a, b) => a.venc.localeCompare(b.venc)).map(r => `<tr><td>${dt(r.venc)}</td><td><strong>${esc(r.cliente)}</strong><div class="muted">${esc(r.ref)}</div></td>
        <td class="num">${brl(r.valor)}${real() && r.id ? `<div><button class="link" data-recebi="${r.id}">recebi</button></div>` : ''}</td></tr>`).join('');
      return `<h1>Contas</h1><p class="sub">Impostos, honorários, fornecedores e o que você anota no WhatsApp. A plataforma não paga: você paga no banco e marca aqui.</p>
      ${real() ? `<details class="card form" style="margin-bottom:12px"><summary><strong>+ Nova conta a pagar ou a receber</strong></summary>
        <label>Tipo<select id="nc-tipo"><option value="pagar">A pagar</option><option value="receber">A receber</option></select></label>
        <label>Descrição (ou cliente, se for a receber)<input id="nc-desc" placeholder="ex.: Aluguel"></label>
        <label>Referência (opcional)<input id="nc-ref" placeholder="ex.: PI 58820"></label>
        <label>Vencimento<input id="nc-venc" type="date"></label>
        <label>Valor<input id="nc-valor" inputmode="decimal" placeholder="ex.: 1.450,00"></label>
        <div class="btns"><button class="primary" id="nc-ok">Guardar</button></div></details>` : ''}
      <div class="card" style="margin-bottom:12px"><strong>Importar do seu grupo do WhatsApp</strong>
        <p class="muted">No grupo: ⋮ › Mais › Exportar conversa › Sem mídia. Cole o texto aqui. Linhas com valor viram conta; o resto é ignorado.</p>
        <textarea id="wa" rows="5" placeholder="Cole aqui a conversa exportada">${esc(D.whatsappExemplo)}</textarea>
        <div class="btns"><button class="primary" id="wa-go">Ler mensagens</button></div><div id="wa-out"></div></div>
      <div class="card" style="margin-bottom:12px"><strong>A pagar</strong>${rows ? `<table><thead><tr><th>Venc.</th><th>Conta</th><th class="num">Valor</th></tr></thead><tbody>${rows}</tbody></table>` : '<p class="muted">Nenhuma conta em aberto.</p>'}</div>
      <div class="card"><strong>A receber</strong>${rec ? `<table><tbody>${rec}</tbody></table>` : '<p class="muted">Nada previsto.</p>'}</div>`;
    },
    documentos() {
      return `<h1>Documentos e regras</h1><p class="sub">Biblioteca da empresa: cada documento é guardado uma vez e reaproveitado em todas as PIs. Para trocar por uma versão nova, toque em "atualizar", escolha o PDF ou tire a foto, e informe a validade.</p>
      <div id="up-form"></div>
      <div class="card" style="margin-bottom:12px"><strong>Certidões e registros</strong><table>
        ${[...D.certidoes].sort((a, b) => (a.validade || '9').localeCompare(b.validade || '9')).map(c => `<tr><td><strong>${esc(c.nome)}</strong>${c.numero ? `<div class="muted">${esc(c.numero)}</div>` : ''}${c.internas ? `<div class="muted">certificado ${sitData(c.validade).txt}</div>` : ''}</td><td class="num"><span class="tag ${situacao(c.nome).cls}">${situacao(c.nome).txt}</span><div><button class="link" data-up="${esc(c.nome)}">atualizar</button>${real() && c.arquivo ? ` · <button class="link" data-ver="${esc(c.arquivo)}">ver</button>` : ''}</div></td></tr>
          ${(c.internas || []).map(i => `<tr class="sub-row"><td>↳ ${esc(i.nome)}</td><td class="num"><span class="tag ${sitData(i.validade).cls}">${sitData(i.validade).txt}</span><div><button class="link" data-up="${esc(c.nome)}|${esc(i.nome)}">atualizar</button></div></td></tr>`).join('')}`).join('')}</table>
        <p class="muted">O certificado de registro tem validade própria, mas cada certidão listada nele vence antes. Certidão interna vencida precisa ir anexada atualizada junto com o certificado.</p></div>
      <div class="card" style="margin-bottom:12px"><strong>Para quem vai cada processo</strong><p class="muted">Cada agência tem um e-mail padrão; algumas têm atendente por cliente. Sem atendente, vai para o padrão.</p><table>
        <thead><tr><th>Agência</th><th>Cliente</th><th>Destinatário</th><th>Manual</th></tr></thead>
        ${D.agencias.map(a => a.atendentes.map(t => `<tr><td>${esc(a.nome)}</td><td>${esc(t.cliente)}</td><td>${esc(t.nome)}<div class="muted">${esc(t.email)}</div></td><td>${manualDe(a.nome, t.cliente) ? '<span class="tag enviado">sim</span>' : '—'}</td></tr>`).join('')
          + `<tr><td>${esc(a.nome)}</td><td class="muted">demais clientes</td><td>padrão<div class="muted">${esc(a.padrao || 'a cadastrar')}</div></td><td>${D.manuais.some(m => m.agencia === a.nome && !a.atendentes.some(t => t.cliente === m.cliente)) ? '<span class="tag enviado">sim</span>' : '—'}</td></tr>`).join('')}</table></div>
      <div class="card"><strong>O que cada órgão exige</strong><p class="muted">Base: ${D.padrao.map(esc).join(', ')}. Órgão ainda não mapeado recebe todos os documentos, como hoje.</p><table>
        <thead><tr><th>Órgão</th><th>Registro</th><th class="hide-sm">Exige também</th><th>Regra</th></tr></thead>
        ${D.orgaos.map(o => `<tr><td>${esc(o.nome)}</td><td>${esc(o.registro)}</td><td class="hide-sm">${o.mapeado ? (o.extras.map(esc).join(', ') || '—') : '—'}</td><td><span class="tag ${o.mapeado ? 'enviado' : 'pendente'}">${o.mapeado ? 'mapeado' : 'envia tudo'}</span></td></tr>`).join('')}</table></div>`;
    },
    resumo() {
      const p7 = abertas().filter(p => p.venc <= addDays(7)).sort((a, b) => a.venc.localeCompare(b.venc));
      const r7 = D.receber.filter(r => r.venc <= addDays(7));
      const pts = fluxo(30), min = pts.reduce((m, p) => p.s < m.s ? p : m, pts[0]);
      const alertas = D.certidoes.filter(c => c.validade && diasAte(c.validade) <= 15);
      const msg = `*${real() ? D.empresa.nome : 'FATO67'} · Resumo de ${dt(iso(today))}*

Saldo PJ (C6): ${brl(pjF())}
Contas PF: ${brl(pfF())}

*A pagar nos próximos 7 dias*
${p7.map(p => `• ${dt(p.venc)} ${p.desc}: ${brl(p.valor)}`).join('\n') || '• nada previsto'}

*A receber nos próximos 7 dias*
${r7.map(r => `• ${dt(r.venc)} ${r.ref || r.cliente}: ${brl(r.valor)}`).join('\n') || '• nada previsto'}

Menor saldo PJ em 30 dias: ${brl(min.s)} em ${dt(min.day)}

*Certidões*
${alertas.map(c => `• ${c.nome}: ${situacao(c.nome).txt}`).join('\n') || '• todas em dia'}

Abrir: economistarenato.com.br/fato67`;
      return `<h1>Resumo diário</h1><p class="sub">${real() ? 'O envio automático pelo WhatsApp vem numa próxima etapa. Por enquanto, copie e mande para você mesmo.' : 'Chega todo dia às 7h no seu WhatsApp.'} Prévia de hoje:</p>
      <div class="phone"><div class="bubble">${esc(msg).replace(/\*(.+?)\*/g, '<strong>$1</strong>')}</div></div>
      ${real() ? `<div class="btns" style="justify-content:center"><a class="btn primary" href="https://wa.me/?text=${encodeURIComponent(msg)}" target="_blank" rel="noopener">Mandar pelo WhatsApp</a></div>` : ''}`;
    }
  };

  // Ação no banco: trava a tela, grava, recarrega e redesenha
  async function acao(fn, okTxt) {
    document.body.classList.add('ocupado');
    try { await fn(); await recarregar(); render(); if (okTxt) avisar(okTxt); }
    catch (e) { avisar('Não foi possível gravar: ' + e.message, 'bad'); }
    finally { document.body.classList.remove('ocupado'); }
  }
  const valorBR = s => window.Extrato.num(s);

  function bind(route) {
    const go = document.getElementById('wa-go');
    if (go) go.addEventListener('click', () => {
      const keep = document.getElementById('wa').value;
      const novas = parseWhats(keep);
      importadas = novas;
      render(); document.getElementById('wa').value = keep;
      document.getElementById('wa-out').innerHTML = !novas.length ? '<p class="bad">Nenhuma linha com valor encontrada.</p>'
        : real() ? `<p class="good">${novas.length} contas encontradas (marcadas "importada agora" na lista). Confira e guarde.</p><div class="btns"><button class="primary" id="wa-save">Guardar ${novas.length} contas</button><button id="wa-x">Descartar</button></div>`
        : `<p class="good">${novas.length} contas encontradas e adicionadas na lista.</p>`;
      const sv = document.getElementById('wa-save');
      if (sv) sv.onclick = () => acao(async () => { await N.acoes.salvarContas(importadas); importadas = []; }, 'Contas guardadas.');
      const x = document.getElementById('wa-x'); if (x) x.onclick = () => { importadas = []; render(); };
    });
    document.querySelectorAll('input[data-doc]').forEach(cb => cb.addEventListener('change', () => {
      const pi = piAtual(), n = cb.dataset.doc;
      pi.sel = cb.checked ? docsPi(pi).concat([n]) : docsPi(pi).filter(x => x !== n);
      if (real()) acao(() => N.acoes.anexosPi(pi.id, pi.sel)); else render();
    }));
    document.querySelectorAll('input[data-passo]').forEach(cb => cb.addEventListener('change', () => {
      if (!real()) return; const pi = piAtual();
      acao(() => N.acoes.passosPi(pi.id, cb.checked ? +cb.dataset.passo + 1 : +cb.dataset.passo));
    }));
    document.querySelectorAll('input.pi-up').forEach(inp => inp.addEventListener('change', () => {
      const files = [...inp.files]; if (!files.length) return; const pi = piAtual(), tipo = inp.dataset.tipo;
      if (!real()) { pi.sel = docsPi(pi).concat([files[0].name]); render(); return; }
      acao(async () => {
        for (const f of files) await N.acoes.arquivoPi(pi.id, tipo, f);
        if (tipo === 'avulso') await N.acoes.anexosPi(pi.id, docsPi(pi).concat(files.map(f => f.name)));
      }, 'Arquivo guardado na pasta da PI.');
    }));
    const env = document.getElementById('pi-enviada');
    if (env) env.addEventListener('click', () => acao(() => N.acoes.statusPi(piAtual().id, 'enviada'), 'PI marcada como enviada.'));
    document.querySelectorAll('button[data-up]').forEach(btn => btn.addEventListener('click', () => {
      const [c, i] = btn.dataset.up.split('|');
      document.getElementById('up-form').innerHTML = `<div class="card form" style="margin-bottom:12px"><strong>Atualizar: ${esc(i || c)}</strong>
        <label>Arquivo (PDF ou foto)<input type="file" id="up-f" accept="application/pdf,image/*"></label>
        <label>Válido até<input type="date" id="up-d"></label>
        <div class="btns"><button class="primary" id="up-ok">Guardar</button><button id="up-x">Cancelar</button></div>
        <p class="muted">${real() ? 'O arquivo vai para o armazenamento privado da empresa. A versão anterior fica guardada.' : 'Demonstração: o arquivo fica só neste aparelho. Na versão final, vai para o armazenamento da plataforma, com login.'}</p></div>`;
      window.scrollTo(0, 0);
      document.getElementById('up-x').onclick = () => { document.getElementById('up-form').innerHTML = ''; };
      document.getElementById('up-ok').onclick = () => {
        const v = document.getElementById('up-d').value, f = document.getElementById('up-f').files[0];
        if (!v && !f) { document.getElementById('up-d').focus(); return; }
        const alvo = cert(c);
        if (real()) { acao(() => N.acoes.atualizarDocumento(alvo, i, f, v || null), 'Documento atualizado.'); return; }
        if (i) alvo.internas.find(x => x.nome === i).validade = v; else alvo.validade = v; render();
      };
    }));
    document.querySelectorAll('button[data-ver]').forEach(b => b.addEventListener('click', async () => {
      try { const blob = await N.baixar(b.dataset.ver); window.open(URL.createObjectURL(blob), '_blank'); } catch (e) { avisar(e.message, 'bad'); }
    }));
    document.querySelectorAll('button[data-in]').forEach(b => b.addEventListener('click', () => {
      const e = D.entrada[+b.dataset.in];
      if (real()) acao(() => N.acoes.resolverEntrada(e.id), 'Guardado.'); else { e.feito = true; render(); }
    }));
    document.querySelectorAll('button[data-in-x]').forEach(b => b.addEventListener('click', () => {
      if (real()) acao(() => N.acoes.resolverEntrada(D.entrada[+b.dataset.inX].id)); else { D.entrada.splice(+b.dataset.inX, 1); render(); }
    }));
    document.querySelectorAll('button[data-paga]').forEach(b => b.addEventListener('click', () => acao(() => N.acoes.marcarPaga(b.dataset.paga), 'Conta marcada como paga.')));
    document.querySelectorAll('button[data-recebi]').forEach(b => b.addEventListener('click', () => acao(() => N.acoes.marcarRecebido(b.dataset.recebi), 'Marcado como recebido.')));
    const nc = document.getElementById('nc-ok');
    if (nc) nc.addEventListener('click', () => {
      const g = id => document.getElementById(id).value.trim();
      const valor = valorBR(g('nc-valor')), venc = g('nc-venc'), desc = g('nc-desc');
      if (!desc || !venc || !(valor > 0)) { avisar('Preencha descrição, vencimento e valor.', 'bad'); return; }
      acao(() => g('nc-tipo') === 'receber' ? N.acoes.novoReceber({ cliente: desc, ref: g('nc-ref'), venc, valor }) : N.acoes.novaConta({ desc: g('nc-ref') ? `${desc} (${g('nc-ref')})` : desc, venc, valor, categoria: 'A classificar' }), 'Guardado.');
    });
    // Bancos: saldo digitado e extrato
    const so = document.getElementById('saldo-ok');
    if (so) so.addEventListener('click', () => {
      const itens = [...document.querySelectorAll('input[data-saldo]')].filter(i => i.value.trim()).map(i => ({ conta: i.dataset.saldo, valor: valorBR(i.value) }));
      if (!itens.length) { avisar('Digite ao menos um saldo.', 'bad'); return; }
      if (itens.some(i => isNaN(i.valor))) { avisar('Algum valor não está num formato válido (ex.: 12.345,67).', 'bad'); return; }
      acao(async () => { for (const i of itens) await N.acoes.saldo(i.conta, i.valor); }, 'Saldos guardados.');
    });
    const ef = document.getElementById('ex-file');
    if (ef) ef.addEventListener('change', async () => {
      const f = ef.files[0]; if (!f) return;
      const buf = await f.arrayBuffer();
      let txt = new TextDecoder('utf-8').decode(buf);
      if (txt.includes('�')) txt = new TextDecoder('windows-1252').decode(buf); // OFX de banco costuma vir em Latin-1
      const r = window.Extrato.lerExtrato(f.name, txt), out = document.getElementById('ex-out');
      if (r.erro) { out.innerHTML = `<p class="bad">${esc(r.erro)}</p>`; return; }
      const ent = r.lancamentos.filter(l => l.valor > 0).reduce((a, l) => a + l.valor, 0), sai = r.lancamentos.filter(l => l.valor < 0).reduce((a, l) => a + l.valor, 0);
      const datas = r.lancamentos.map(l => l.data).sort();
      out.innerHTML = `<p><strong>${r.lancamentos.length} lançamentos</strong> de ${dt(datas[0])} a ${dt(datas[datas.length - 1])}: entradas ${brl(ent)}, saídas ${brl(sai)}.${r.saldo ? ` Saldo no arquivo: ${brl(r.saldo.valor)} em ${dt(r.saldo.data)}.` : ''}</p>
        <table>${r.lancamentos.slice(0, 5).map(l => `<tr><td>${dt(l.data)}</td><td>${esc(l.descricao)}</td><td class="num">${brl(l.valor)}</td></tr>`).join('')}</table>
        <div class="btns"><button class="primary" id="ex-ok" ${real() ? '' : 'disabled'}>Importar para ${esc(document.getElementById('ex-conta').selectedOptions[0].text)}</button></div>`;
      const ok = document.getElementById('ex-ok');
      if (ok) ok.onclick = () => { const conta = document.getElementById('ex-conta').value; let n = 0;
        acao(async () => { n = await N.acoes.importarExtrato(conta, r); }).then(() => avisar(`${n} lançamentos novos importados${r.lancamentos.length - n ? `, ${r.lancamentos.length - n} já estavam lá` : ''}.`)); };
    });
    const z = document.getElementById('dl-zip'), pd = document.getElementById('dl-pdf');
    if (z) z.addEventListener('click', () => { z.disabled = true; baixarZip(piAtual()).catch(e => avisar('Erro ao montar o ZIP: ' + e.message, 'bad')).finally(() => { z.disabled = false; }); });
    if (pd) pd.addEventListener('click', () => imprimir(piAtual()));
    const num = document.getElementById('f-num');
    if (num) {
      const upd = () => {
        const pi = { numero: num.value || '_____', orgao: document.getElementById('f-org').value, cliente: document.getElementById('f-cli').value };
        const dst = destino(pi.cliente, pi.orgao);
        const o = orgaoDe(pi.orgao), tudo = document.getElementById('f-tudo').checked;
        const docs = exigidos(pi.orgao, tudo);
        document.getElementById('f-out').innerHTML = `<div class="card" style="margin-top:12px"><strong>Documentos que vão anexados (${docs.length})</strong>${o && !o.mapeado ? '<p class="muted">Este órgão ainda não tem regra; por segurança vai tudo.</p>' : ''}<ul class="alerts">
          ${docs.map(n => `<li><span class="tag ${situacao(n).cls}">${situacao(n).txt}</span> ${esc(n)}</li>`).join('')}</ul>
          <strong>Passos</strong>${manualDe(pi.cliente, pi.orgao) ? '' : '<span class="muted"> (padrão, sem manual para esta combinação)</span>'}<ol>${passos(pi.cliente, pi.orgao).map(t => `<li>${esc(t)}</li>`).join('')}</ol>
          <strong>E-mail</strong><p class="muted">Para: ${esc(dst.txt)}</p><pre class="mail">Para: ${esc(dst.email || '—')}\nAssunto: ${esc(assunto(pi))}\n\n${esc(corpo(pi))}</pre>
          <div class="btns"><button class="primary" id="f-ok" ${real() ? '' : 'disabled title="Desativado na demonstração"'}>Criar PI</button></div></div>`;
        const fo = document.getElementById('f-ok');
        if (fo && real()) fo.onclick = () => {
          const numero = num.value.trim(); if (!numero) { num.focus(); return; }
          if (D.pis.some(p => p.numero === numero)) { avisar('Já existe uma PI com esse número.', 'bad'); return; }
          acao(() => N.acoes.criarPi({ numero, orgao: (o || {}).id || null, agencia: (agenciaDe(pi.cliente) || {}).id || null, anexos: docs }), 'PI criada.')
            .then(() => { location.hash = 'pis/' + encodeURIComponent(numero); });
        };
      };
      ['f-num', 'f-org', 'f-cli', 'f-tudo'].forEach(id => document.getElementById(id).addEventListener('input', upd)); document.getElementById('f-tudo').addEventListener('change', upd); ['f-org', 'f-cli'].forEach(id => document.getElementById(id).addEventListener('change', upd)); upd();
    }
  }
  function render() {
    const [route, sel] = decodeURIComponent(location.hash.slice(1)).split('/');
    const r = views[route] && route !== 'novaPi' ? route : 'painel';
    document.getElementById('app').innerHTML = views[r](sel);
    document.querySelectorAll('nav a').forEach(a => a.classList.toggle('on', a.getAttribute('href') === '#' + r));
    bind(r); window.scrollTo(0, 0);
  }

  // ---- login e troca de modo ----
  let empresaEscolhida = null;
  try { empresaEscolhida = localStorage.getItem('fato67-empresa'); } catch (e) { /* sem storage */ }
  async function recarregar() {
    const dados = await N.carregar(empresaEscolhida);
    if (dados) { D = dados; return true; }
    return false;
  }
  function cabecalho() {
    const btn = document.getElementById('login'), banner = document.getElementById('banner'), selE = document.getElementById('empresa');
    if (real()) {
      btn.textContent = `${primeiro()} · sair`; btn.title = (D.usuario && D.usuario.email) || '';
      banner.hidden = true;
      selE.hidden = D.empresas.length < 2;
      selE.innerHTML = D.empresas.map(e => `<option value="${e.id}" ${e.id === D.empresa.id ? 'selected' : ''}>${esc(e.nome)}</option>`).join('');
    } else {
      btn.textContent = 'Entrar'; banner.hidden = false; selE.hidden = true;
    }
  }
  function telaEntrar() {
    document.getElementById('app').innerHTML = `<div class="card form" style="max-width:420px;margin:24px auto"><h1>Entrar</h1>
      <p class="sub">Use a conta Google do e-mail cadastrado pelo escritório.</p>
      <div class="btns"><button class="primary" id="g-ok" style="width:100%">Entrar com Google</button></div>
      <details style="margin-top:16px"><summary>Entrar com link por e-mail</summary>
        <label>E-mail<input id="m-email" type="email" autocomplete="email"></label>
        <div class="btns"><button id="m-ok">Enviar link</button></div></details>
      <p class="muted" style="margin-top:16px"><a href="#painel" id="demo">Ver a demonstração</a></p></div>`;
    document.getElementById('g-ok').onclick = () => N.entrarGoogle().catch(e => avisar(/provider is not enabled/i.test(e.message) ? 'O login com Google ainda está sendo ligado. Use o link por e-mail.' : e.message, 'bad'));
    document.getElementById('m-ok').onclick = () => { const em = document.getElementById('m-email').value.trim(); if (!em) return;
      N.entrarEmail(em).then(() => avisar('Link enviado. Abra o e-mail neste aparelho.')).catch(e => avisar(e.message, 'bad')); };
    document.getElementById('demo').onclick = () => setTimeout(render, 0);
  }
  document.getElementById('login').addEventListener('click', async () => {
    if (!N) { avisar('Sem conexão com o servidor.', 'bad'); return; }
    if (real()) { await N.sair(); location.reload(); return; }
    telaEntrar();
  });
  document.getElementById('empresa').addEventListener('change', e => {
    empresaEscolhida = e.target.value; try { localStorage.setItem('fato67-empresa', empresaEscolhida); } catch (x) { /* ok */ }
    acao(async () => {}).then(cabecalho);
  });

  async function iniciar() {
    // Quem já entrou antes vê "carregando" em vez da demonstração
    let temSessao = false;
    try { temSessao = Object.keys(localStorage).some(k => /^sb-.*-auth-token/.test(k)) || /[?&]code=/.test(location.search); } catch (e) { /* ok */ }
    if (N && temSessao) document.getElementById('app').innerHTML = '<p class="muted" style="text-align:center;margin-top:48px">Carregando…</p>';
    else render();
    if (!N) return;
    try {
      const u = await N.sessao();
      if (!u) { if (temSessao) render(); return; }
      if (await recarregar()) { cabecalho(); render(); return; }
      document.getElementById('app').innerHTML = `<div class="card" style="max-width:480px;margin:24px auto"><h1>Acesso ainda não liberado</h1>
        <p>Você entrou como <strong>${esc(u.email)}</strong>, mas este e-mail ainda não está ligado a nenhuma empresa. Peça ao escritório para liberar o acesso.</p>
        <div class="btns"><button id="sair2">Sair</button></div></div>`;
      document.getElementById('login').textContent = 'Sair'; D = { ...D, real: false };
      document.getElementById('sair2').onclick = () => N.sair().then(() => location.reload());
    } catch (e) { render(); avisar('Erro ao carregar os dados: ' + e.message, 'bad'); }
  }
  window.addEventListener('hashchange', render);
  iniciar();
  if ('serviceWorker' in navigator && location.protocol === 'https:') navigator.serviceWorker.register('sw.js').catch(() => {});
})();
