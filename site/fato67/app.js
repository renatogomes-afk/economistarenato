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
  // Cliente (órgão) mapeado: só a lista que ele exige. Não mapeado (ou "enviar tudo"): todas as certidões, mais o registro desse órgão.
  // Certificado de registro cadastral (CERCA, CRC): um documento só, emitido pelo órgão, que lista certidões internas
  const ehRegistro = n => D.orgaos.some(x => x.registro === n) || /cerca|crc|registro cadastral/i.test(n) || !!(cert(n) && cert(n).internas);
  const registrosDe = o => o ? [...new Set((o.registro ? [o.registro] : []).concat(o.extras.filter(ehRegistro)))] : [];
  const exigidos = (orgao, tudo) => {
    const o = orgaoDe(orgao);
    if (!o || tudo || !o.mapeado) return D.certidoes.filter(c => !ehRegistro(c.nome)).map(c => c.nome).concat(registrosDe(o));
    return o.extras.concat(o.registro && !o.extras.includes(o.registro) ? [o.registro] : []);
  };
  // Mês-competência (AAAA-MM) de um documento, NF ou print
  const mesDe = x => String(x.competencia || x.criado || iso(today)).slice(0, 7);
  const nomeMes = m => { const [a, mm] = m.split('-'); return ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'][+mm - 1] + '/' + a; };
  let mesArq = null;
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

  const fmt = v => v.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  // Saldo do dia: C6 PJ já preenchido com o último valor (corrige só se mudou); contas PF opcionais
  function cartaoSaldo(noInicio) {
    const hoje = iso(today), pj = D.saldos.filter(s => s.tipo === 'PJ'), pf = D.saldos.filter(s => s.tipo !== 'PJ');
    const campo = (s, pre) => `<label>${esc(s.conta)} <span class="muted">${s.data ? `· ${s.data === hoje ? 'hoje' : 'último em ' + dt(s.data)}: ${brl(s.saldo)}` : ''}</span>
      <input inputmode="decimal" data-saldo="${esc(s.id || s.conta)}" ${pre && s.data ? `value="${fmt(s.saldo)}"` : ''} placeholder="${s.data ? fmt(s.saldo) : 'ex.: 12.345,67'}"></label>`;
    return `<div class="card form destaque" style="margin-bottom:12px"><strong>Saldo de hoje</strong>
      <p class="muted">${noInicio ? 'Abra o app do C6, confira o saldo PJ e corrija se mudou.' : 'Abra o app do banco, veja o saldo e digite aqui.'}</p>
      ${pj.map(s => campo(s, true)).join('')}
      ${pf.length ? `<details${noInicio ? '' : ' open'}><summary>Contas PF (opcional)</summary>${pf.map(s => campo(s, false)).join('')}</details>` : ''}
      <div class="btns"><button class="primary" id="saldo-ok" ${real() ? '' : 'disabled title="Demonstração"'}>Guardar</button>${noInicio ? '<a class="btn" href="#contas">Importar extrato</a>' : ''}</div></div>`;
  }
  // Próxima ação da PI, para o topo da tela e para a lista do dia
  function proximo(pi) {
    if (pi.status === 'enviada') return { cls: 'enviado', txt: 'Enviada.' };
    const ruins = docsPi(pi).filter(n => situacao(n).cls === 'classificar' && !(pi.avulsos || []).includes(n));
    if (ruins.length) return { cls: 'classificar', txt: `Falta atualizar: ${ruins.join(', ')}.`, docs: true };
    const lista = l => l.length > 3 ? `${l.slice(0, 3).join(', ')} e mais ${l.length - 3}` : l.join(', ');
    const semArq = docsPi(pi).filter(n => cert(n) && cert(n).semArquivo);
    if (semArq.length) return { cls: 'pendente', txt: `Falta guardar o PDF de: ${lista(semArq)}.`, docs: true };
    if (!pi.pasta.nf) return { cls: 'pendente', txt: 'Falta anexar a NF.', nf: true };
    if (!pi.pasta.prints.length) return { cls: 'pendente', txt: 'Falta anexar os prints de veiculação.', prints: true };
    return { cls: 'enviado', txt: 'Pronta: baixe o ZIP, abra o e-mail, anexe e envie.' };
  }
  function textoResumo() {
    const p7 = abertas().filter(p => p.venc <= addDays(7)).sort((a, b) => a.venc.localeCompare(b.venc));
    const r7 = D.receber.filter(r => r.venc <= addDays(7));
    const pts = fluxo(30), min = pts.reduce((m, p) => p.s < m.s ? p : m, pts[0]);
    const alertas = D.certidoes.filter(c => c.validade && diasAte(c.validade) <= 15);
    return `*${real() ? D.empresa.nome : 'FATO67'} · Resumo de ${dt(iso(today))}*

Saldo PJ: ${brl(pjF())}
Contas PF: ${brl(pfF())}

*A pagar nos próximos 7 dias*
${p7.map(p => `• ${dt(p.venc)} ${p.desc}: ${brl(p.valor)}`).join('\n') || '• nada previsto'}

*A receber nos próximos 7 dias*
${r7.map(r => `• ${dt(r.venc)} ${r.ref || r.cliente}: ${brl(r.valor)}`).join('\n') || '• nada previsto'}

Menor saldo PJ em 30 dias: ${brl(min.s)} em ${dt(min.day)}

*Certidões*
${alertas.map(c => `• ${c.nome}: ${situacao(c.nome).txt}`).join('\n') || '• todas em dia'}

Abrir: economistarenato.com.br/fato67`;
  }

  const views = {
    rotinas() {
      const hoje = iso(today);
      const saldoPend = D.saldos.filter(s => s.tipo === 'PJ' && s.data !== hoje);
      // "Para fazer hoje": tudo que pede um toque, com a ação na própria linha
      const t = [];
      abertas().filter(p => p.venc <= addDays(1)).sort((a, b) => a.venc.localeCompare(b.venc)).forEach(p => t.push(
        `<li class="todo"><div><strong>Pagar ${esc(p.desc)}</strong> · ${brl(p.valor)}<div class="${p.venc < hoje ? 'bad' : 'muted'}">${p.venc < hoje ? `vencida em ${dt(p.venc)}` : p.venc === hoje ? 'vence hoje' : 'vence amanhã'}</div></div>${real() && p.id ? `<button data-paga="${p.id}">Paguei</button>` : ''}</li>`));
      D.receber.filter(r => r.venc <= hoje).forEach(r => t.push(
        `<li class="todo"><div><strong>Receber de ${esc(r.cliente)}</strong> · ${brl(r.valor)}<div class="muted">${esc(r.ref)} · previsto para ${dt(r.venc)}</div></div>${real() && r.id ? `<button data-recebi="${r.id}">Recebi</button>` : ''}</li>`));
      D.certidoes.filter(c => ['classificar'].includes(situacao(c.nome).cls) || (c.validade && diasAte(c.validade) <= 15)).forEach(c => t.push(
        `<li class="todo"><div><strong>${esc(c.nome)}</strong><div class="${situacao(c.nome).cls === 'classificar' ? 'bad' : 'muted'}">${situacao(c.nome).txt}</div></div><a class="btn" href="#arquivo">Atualizar</a></li>`));
      D.pis.filter(p => p.status !== 'enviada').forEach(p => t.push(
        `<li class="todo"><div><strong>PI ${esc(p.numero)}</strong> · ${esc(p.orgao)}<div class="muted">${esc(proximo(p).txt)}</div></div><a class="btn" href="#pis/${encodeURIComponent(p.numero)}">Abrir</a></li>`));
      const semConc = (D.extrato || []).filter(x => x.id && !x.conciliado).length;
      if (semConc) t.push(`<li class="todo"><div><strong>Conciliar o extrato</strong><div class="muted">${semConc} lançamento(s) ainda sem conta ligada</div></div><a class="btn" href="#contas">Conciliar</a></li>`);
      D.entrada.forEach((e, i) => { if (!e.feito) t.push(
        `<li class="todo"><div><strong>Chegou: ${esc(e.arquivo)}</strong><div class="muted">de ${esc(e.de)} · parece: ${esc(e.parece)}</div></div><span class="btns" style="margin:0"><button class="primary" data-in="${i}">Guardar</button><button data-in-x="${i}" aria-label="Descartar">✕</button></span></li>`); });
      // Rotinas fixas da empresa, cada uma com a situação de agora
      const ext = D.extrato || [], ultExt = ext.length ? ext.map(x => x.data).sort().pop() : null;
      const certRuins = D.certidoes.filter(c => situacao(c.nome).cls !== 'enviado').length;
      const emAndamento = D.pis.filter(p => p.status !== 'enviada').length;
      const rot = [
        ['Todo dia', 'Informar o saldo do C6 PJ', saldoPend.length ? ['pendente', 'falta hoje'] : ['enviado', 'feito hoje'], '#contas'],
        ['Todo dia', 'Lançar as contas anotadas no grupo do WhatsApp', null, '#contas'],
        ['Toda semana', 'Importar o extrato e conciliar', !ultExt ? ['pendente', 'nenhum extrato'] : semConc ? ['pendente', `${semConc} sem conciliar`] : diasAte(ultExt) < -7 ? ['pendente', `último em ${dt(ultExt)}`] : ['enviado', 'em dia'], '#contas'],
        ['Todo mês', `Arquivo de ${nomeMes(iso(today).slice(0, 7))}: manter certidões e registros em dia`, certRuins ? ['classificar', `${certRuins} para atualizar`] : ['enviado', 'em dia'], '#arquivo'],
        ['A cada PI', 'NF, prints e envio do processo', emAndamento ? ['pendente', `${emAndamento} em andamento`] : ['enviado', 'nenhuma pendente'], '#pis']];
      return `<h1>${saudacao()}, ${esc(primeiro())}</h1><p class="sub">Rotinas de ${dt(hoje)}${real() ? ' · ' + esc(D.empresa.nome) : ''}</p>
      ${saldoPend.length ? cartaoSaldo(true) : ''}
      <div class="card" style="margin-bottom:12px"><strong>Para fazer hoje</strong>
        ${t.length ? `<ul class="alerts">${t.join('')}</ul>` : `<p class="good" style="margin:8px 0 0">Tudo em dia.${saldoPend.length ? ' Só falta o saldo acima.' : ''}</p>`}</div>
      <div class="card"><strong>Rotinas da empresa</strong><ul class="alerts">${rot.map(([q, o, st, h]) => `<li class="todo"><div><span class="muted">${q}</span><div><strong>${o}</strong></div></div>${st ? `<a href="${h}"><span class="tag ${st[0]}">${st[1]}</span></a>` : `<a class="btn" href="${h}">Abrir</a>`}</li>`).join('')}</ul></div>`;
    },
    painel() {
      const hoje = iso(today);
      const pts = fluxo(30), min = pts.reduce((m, p) => p.s < m.s ? p : m, pts[0]);
      const p7 = abertas().filter(p => p.venc <= addDays(7)).reduce((a, p) => a + p.valor, 0);
      const r7 = D.receber.filter(r => r.venc <= addDays(7)).reduce((a, r) => a + r.valor, 0);
      const prox = abertas().filter(p => p.venc <= addDays(7)).map(p => ({ d: p.venc, txt: p.desc, v: -p.valor }))
        .concat(D.receber.filter(r => r.venc <= addDays(7)).map(r => ({ d: r.venc, txt: `${r.cliente}${r.ref ? ' · ' + r.ref : ''}`, v: r.valor }))).sort((a, b) => a.d.localeCompare(b.d));
      return `<h1>Painel financeiro</h1><p class="sub">Acompanhamento de ${dt(hoje)}${real() ? ' · ' + esc(D.empresa.nome) : ''}. Para lançar e conciliar, use Contas.</p>
      <div class="grid">
        <div class="card kpi"><div class="label">Saldo PJ</div><div class="value">${brl(pjF())}</div></div>
        <div class="card kpi"><div class="label">A pagar em 7 dias</div><div class="value bad">${brl(p7)}</div></div>
        <div class="card kpi"><div class="label">A receber em 7 dias</div><div class="value good">${brl(r7)}</div></div>
        <div class="card kpi"><div class="label">Menor saldo em 30 dias</div><div class="value ${min.s < 0 ? 'bad' : ''}">${brl(min.s)}</div><div class="label">em ${dt(min.day)}</div></div>
      </div>
      <div class="card chart"><strong>Fluxo de caixa PJ, 30 dias</strong><p class="muted" style="margin:4px 0 8px">Saldo de hoje menos contas a pagar, mais recebimentos previstos.</p>${chart(pts)}</div>
      <div class="card" style="margin-top:12px"><strong>Próximos 7 dias</strong>${prox.length ? `<table>${prox.map(x => `<tr><td>${dt(x.d)}${x.d < hoje ? '<div class="bad">atrasado</div>' : ''}</td><td>${esc(x.txt)}</td><td class="num ${x.v < 0 ? 'bad' : 'good'}">${brl(x.v)}</td></tr>`).join('')}</table>` : '<p class="muted">Nada previsto.</p>'}</div>
      <div class="card" style="margin-top:12px"><strong>Saldos por conta</strong><table>${D.saldos.map(s => `<tr><td>${esc(s.conta)}${s.data ? `<div class="muted">em ${dt(s.data)}</div>` : real() ? '<div class="muted">saldo ainda não informado</div>' : ''}</td><td class="num">${brl(s.saldo)}</td></tr>`).join('')}<tr><td><strong>Total PF</strong></td><td class="num"><strong>${brl(pfF())}</strong></td></tr></table></div>
      <div class="card" style="margin-top:12px"><strong>Resumo do dia</strong><p class="muted">Saldos, contas da semana, menor saldo do mês e certidões, pronto para o WhatsApp.</p>
        <div class="btns"><a class="btn primary" href="https://wa.me/?text=${encodeURIComponent(textoResumo())}" target="_blank" rel="noopener">Mandar no WhatsApp</a><a class="btn" href="#resumo">Ver antes</a></div></div>`;
    },
    contas() {
      const contas = D.saldos, ext = D.extrato || [], hoje = iso(today);
      const abertasP = pagarTodas().filter(p => p.status !== 'pago' && p.id), rec = D.receber.filter(r => r.id);
      const pend = ext.filter(x => !x.conciliado && x.id);
      const dist = (a, b) => Math.abs(new Date(a) - new Date(b)) / 864e5;
      const par = x => (x.valor < 0 ? abertasP : rec).filter(c => Math.abs(c.valor - Math.abs(x.valor)) < 0.01 && dist(c.venc, x.data) <= 10).sort((c1, c2) => dist(c1.venc, x.data) - dist(c2.venc, x.data))[0];
      const rows = [...pagarTodas()].filter(p => p.status !== 'pago').sort((a, b) => a.venc.localeCompare(b.venc)).map(p => `<tr>
        <td>${dt(p.venc)}${p.venc < hoje ? '<div class="bad">vencida</div>' : ''}</td><td><strong>${esc(p.desc)}</strong><div class="muted">${esc(p.origem)}${p.importada ? ' · importada agora' : ''}</div></td>
        <td class="num">${brl(p.valor)}${real() && p.id ? `<div><button class="link" data-paga="${p.id}">paguei</button></div>` : ''}</td></tr>`).join('');
      const recRows = [...D.receber].sort((a, b) => a.venc.localeCompare(b.venc)).map(r => `<tr><td>${dt(r.venc)}</td><td><strong>${esc(r.cliente)}</strong><div class="muted">${esc(r.ref)}</div></td>
        <td class="num">${brl(r.valor)}${real() && r.id ? `<div><button class="link" data-recebi="${r.id}">recebi</button></div>` : ''}</td></tr>`).join('');
      return `<h1>Contas</h1><p class="sub">Linha de produção em três etapas: lançar as contas, atualizar o banco e conciliar um com o outro.</p>
      <h2 class="etapa"><span>1</span> Lançar contas a pagar e a receber</h2>
      <details class="card form" style="margin-bottom:12px"><summary><strong>+ Nova conta</strong></summary>
        <div class="seg" role="group"><button type="button" class="on" data-nc="pagar">A pagar</button><button type="button" data-nc="receber">A receber</button></div><input type="hidden" id="nc-tipo" value="pagar">
        <label><span id="nc-l1">Descrição</span><input id="nc-desc" placeholder="ex.: Aluguel"></label>
        <label><span id="nc-l2">Observação (opcional)</span><input id="nc-ref" placeholder="ex.: fornecedor, nº do boleto"></label>
        <label>Vencimento<input id="nc-venc" type="date"></label>
        <label>Valor<input id="nc-valor" inputmode="decimal" placeholder="ex.: 1.450,00"></label>
        <div class="btns"><button class="primary" id="nc-ok" ${real() ? '' : 'disabled'}>Guardar</button></div></details>
      <details class="card" style="margin-bottom:12px"${importadas.length ? ' open' : ''}><summary><strong>Importar do grupo do WhatsApp</strong></summary>
        <p class="muted">No grupo: ⋮ › Mais › Exportar conversa › Sem mídia. Cole o texto aqui. Linhas com valor viram conta; o resto é ignorado.</p>
        <textarea id="wa" rows="5" placeholder="Cole aqui a conversa exportada">${esc(D.whatsappExemplo)}</textarea>
        <div class="btns"><button class="primary" id="wa-go">Ler mensagens</button></div><div id="wa-out"></div></details>
      <h2 class="etapa"><span>2</span> Atualizar o banco</h2>
      ${cartaoSaldo(false)}
      <div class="card form" style="margin-bottom:12px"><strong>Importar extrato</strong>
        <p class="muted">C6 e Banco do Brasil: extrato › exportar › OFX. Mercado Pago: Seu dinheiro › Relatórios › CSV. Importar de novo o mesmo período não duplica.</p>
        <label>Conta<select id="ex-conta">${contas.map(s => `<option value="${esc(s.id || '')}">${esc(s.conta)}</option>`).join('')}</select></label>
        <label>Arquivo (.ofx ou .csv)<input type="file" id="ex-file" accept=".ofx,.csv,.txt,text/csv,application/x-ofx"></label>
        <div id="ex-out"></div></div>
      <h2 class="etapa"><span>3</span> Conciliar extrato com contas</h2>
      <div class="card" style="margin-bottom:12px">${pend.length ? `<p class="muted" style="margin-top:0">Cada lançamento do extrato precisa ser ligado a uma conta. Quando valor e data batem, a plataforma sugere; senão, lance como conta nova ou ignore (transferência entre contas, por exemplo).</p><ul class="alerts">${pend.map(x => { const c = par(x);
          return `<li class="todo"><div><strong>${dt(x.data)} · <span class="${x.valor < 0 ? 'bad' : 'good'}">${brl(x.valor)}</span></strong><div>${esc(x.descricao)}</div><div class="muted">${esc((contas.find(k => k.id === x.conta_id) || {}).conta)}${c ? ` · bate com: <strong>${esc(c.desc || c.cliente)}</strong> (venc. ${dt(c.venc)})` : ' · sem conta correspondente'}</div></div>
            <span class="btns col" style="margin:0">${c ? `<button class="primary" data-conc="${x.id}|${c.id}">Conciliar</button>` : `<button data-lanc="${x.id}">Lançar</button>`}<button class="link" data-ign="${x.id}">ignorar</button></span></li>`; }).join('')}</ul>`
        : `<p class="${ext.length ? 'good' : 'muted'}" style="margin:0">${ext.length ? 'Tudo conciliado.' : 'Importe um extrato na etapa 2 para conciliar.'}</p>`}</div>
      <h2 class="etapa">Em aberto</h2>
      <div class="card" style="margin-bottom:12px"><strong>A pagar</strong>${rows ? `<table><thead><tr><th>Venc.</th><th>Conta</th><th class="num">Valor</th></tr></thead><tbody>${rows}</tbody></table>` : '<p class="muted">Nenhuma conta em aberto.</p>'}</div>
      <div class="card" style="margin-bottom:12px"><strong>A receber</strong>${recRows ? `<table><tbody>${recRows}</tbody></table>` : '<p class="muted">Nada previsto.</p>'}</div>
      ${ext.length ? `<details class="card"><summary><strong>Últimos lançamentos do extrato</strong></summary><table>${ext.slice(0, 40).map(x => `<tr><td>${dt(x.data)}</td><td>${esc(x.descricao)}<div class="muted">${esc((contas.find(c => c.id === x.conta_id) || {}).conta)}${x.conciliado ? ' · conciliado' : ''}</div></td><td class="num ${x.valor < 0 ? 'bad' : 'good'}">${brl(x.valor)}</td></tr>`).join('')}</table></details>` : ''}`;
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
        const px = proximo(pi), up = (tipo, txt, multi) => real() ? `<label class="btn up${multi === 'p' ? ' primary' : ''}">${txt}<input type="file" class="pi-up" data-tipo="${tipo}" accept="${tipo === 'print' ? 'image/*,application/pdf' : 'application/pdf,image/*'}" ${tipo === 'print' ? 'multiple' : ''} hidden></label>` : '';
        const mail = real() && dst.email ? `<a class="btn${px.cls === 'enviado' && pi.status !== 'enviada' ? ' primary' : ''}" href="mailto:${esc(dst.email)}?subject=${encodeURIComponent(assunto(pi))}&body=${encodeURIComponent(corpo(pi))}">Abrir e-mail</a>` : '';
        return `<p><a href="#pis">← PIs</a></p><h1>PI ${esc(pi.numero)}</h1><p class="sub">${esc(pi.orgao)} · ${esc(pi.cliente)}</p>
        <div class="card destaque" style="margin-bottom:12px"><span class="tag ${px.cls}">${pi.status === 'enviada' ? 'enviada' : px.cls === 'enviado' ? 'pronta' : 'pendente'}</span>
          <p style="margin:8px 0 0"><strong>${esc(px.txt)}</strong></p>
          <div class="btns wrap">${px.nf ? up('nf', '+ Anexar NF', 'p') : ''}${px.prints ? up('print', '+ Anexar prints', 'p') : ''}${px.docs ? '<a class="btn primary" href="#arquivo">Atualizar documentos</a>' : ''}
            <button id="dl-zip" class="${px.cls === 'enviado' && pi.status !== 'enviada' ? 'primary' : ''}">Baixar ZIP</button>${mail}
            ${real() && pi.status !== 'enviada' ? '<button id="pi-enviada">Marcar como enviada</button>' : ''}</div>
          ${real() && !dst.email ? '<p class="muted">A agência ainda não tem e-mail cadastrado; o e-mail abre sem destinatário.</p>' : ''}</div>
        <details class="card" style="margin-bottom:12px"${px.docs ? ' open' : ''}><summary><strong>Documentos anexados (${docs.length})</strong></summary>
          <p class="muted">${o && o.mapeado ? 'Marcados pela regra do órgão.' : 'Órgão sem regra: tudo marcado.'} Toque para tirar ou incluir.</p>
          <ul class="alerts">${docs.map(n => linha(n, true)).join('')}</ul>
          ${outros.length ? `<details><summary>Incluir outro documento da biblioteca (${outros.length})</summary><ul class="alerts">${outros.map(n => linha(n, false)).join('')}</ul></details>` : ''}
          <label class="btn up">+ Anexar arquivo só nesta PI<input type="file" class="pi-up" data-tipo="avulso" accept="application/pdf,image/*" hidden></label></details>
        <details class="card" style="margin-bottom:12px"><summary><strong>Ver o e-mail</strong></summary>
          <p class="muted">Para: ${esc(dst.txt)}</p><pre class="mail">Para: ${esc(dst.email || '—')}\nAssunto: ${esc(assunto(pi))}\n\n${esc(corpo(pi))}\n\nAnexos: ${docs.map(esc).join('; ')}</pre>
          <p class="muted">Baixe o ZIP e anexe no e-mail. O envio pela própria plataforma vem depois.</p></details>
        <div class="card" style="margin-bottom:12px"><strong>Nota fiscal e prints</strong><ul class="alerts">
          <li>Nota fiscal: ${pi.pasta.nf ? esc(pi.pasta.nf) : '<span class="tag pendente">ainda não anexada</span>'}</li>
          <li>Prints de veiculação: ${pi.pasta.prints.map(esc).join(', ') || '<span class="tag pendente">nenhum</span>'}</li></ul>
          <div class="btns wrap">${up('nf', pi.pasta.nf ? 'Trocar NF' : '+ NF')}${up('print', '+ Prints')}<button id="dl-pdf">PDF para imprimir</button></div></div>
        <details class="card"><summary><strong>Passos do processo</strong> <span class="muted">(${pi.status === 'enviada' ? 'todos' : Math.min(pi.feitos || 0, passos(pi.cliente, pi.orgao).length)} de ${passos(pi.cliente, pi.orgao).length})</span></summary><p class="muted">${manualDe(pi.cliente, pi.orgao) ? `Do manual "${esc(pi.cliente)} + ${esc(pi.orgao)}".` : 'Passos padrão: ainda não há manual para esta combinação.'}</p>
          <ul class="alerts">${passos(pi.cliente, pi.orgao).map((t, i) => `<li><label class="pick"><input type="checkbox" data-passo="${i}" ${pi.status === 'enviada' || i < (pi.feitos || 0) ? 'checked' : ''}><span>${esc(t)}</span></label></li>`).join('')}</ul></details>
        ${real() ? '<div style="margin-top:24px;text-align:center"><button class="link perigo" id="pi-excluir">Excluir esta PI</button></div>' : ''}`;
      }
      const etapas = [
        ['Falta documento', 'classificar', p => p.status !== 'enviada' && proximo(p).docs],
        ['Falta NF ou prints', 'pendente', p => p.status !== 'enviada' && !proximo(p).docs && (proximo(p).nf || proximo(p).prints)],
        ['Pronta para enviar', 'enviado', p => p.status !== 'enviada' && proximo(p).cls === 'enviado'],
        ['Enviadas', 'enviado', p => p.status === 'enviada']];
      const cartao = p => `<a class="card picard" href="#pis/${encodeURIComponent(p.numero)}"><div><strong>PI ${esc(p.numero)}</strong> · ${esc(p.orgao)}<div class="muted">${esc(p.cliente)} · ${dt(p.data)}</div>${p.status !== 'enviada' ? `<div class="muted">${esc(proximo(p).txt)}</div>` : ''}</div><span class="seta">›</span></a>`;
      return `<div class="head"><div><h1>Envios</h1><p class="sub">Linha de produção dos e-mails: cada PI anda da esquerda para a direita até ser enviada.</p></div><a class="btn primary" href="#pis/nova">+ Nova PI</a></div>
      <div class="trilha">${etapas.map(([n, c, f]) => `<span class="tag ${D.pis.filter(f).length ? c : ''}">${n}: ${D.pis.filter(f).length}</span>`).join('<span class="muted">›</span>')}</div>
      ${D.pis.length ? '' : '<p class="muted">Nenhuma PI cadastrada ainda.</p>'}
      ${etapas.map(([n, c, f], i) => { const l = D.pis.filter(f); if (!l.length) return '';
        return i === 3 ? `<details style="margin-top:16px"><summary><strong>${n} (${l.length})</strong></summary>${l.map(cartao).join('')}</details>` : `<h2 class="etapa"><span>${i + 1}</span> ${n}</h2>${l.map(cartao).join('')}`; }).join('')}`;
    },
    novaPi() {
      return `<p><a href="#pis">← PIs</a></p><h1>Nova PI</h1><p class="sub">Escolha o órgão e a plataforma junta os documentos certos e monta o e-mail.</p>
      <div class="card form"><label>Número da PI<input id="f-num" inputmode="numeric" placeholder="ex.: 10250"></label>
        <label>Cliente final (órgão)<select id="f-org">${D.orgaos.map(o => `<option>${esc(o.nome)}</option>`).join('')}</select></label>
        <label>Agência<select id="f-cli">${D.agencias.map(a => `<option>${esc(a.nome)}</option>`).join('')}</select></label>
        <label class="check"><input id="f-tudo" type="checkbox"> Enviar todos os documentos, mesmo os que o órgão não exige</label></div>
      <div id="f-out"></div>`;
    },
    arquivo() {
      const atual = iso(today).slice(0, 7), M = mesArq && mesArq <= atual ? mesArq : atual, agora = M === atual;
      const arqs = D.pis.flatMap(p => (p.pasta.arquivos || [{ tipo: 'nf', nome: p.pasta.nf }].concat(p.pasta.prints.map(n => ({ tipo: 'print', nome: n })))).filter(a => a.nome)
        .map(a => ({ ...a, pi: p, mes: a.competencia ? a.competencia.slice(0, 7) : String(p.data || iso(today)).slice(0, 7) })));
      // Meses com alguma coisa guardada, do mais antigo até o atual (sem buracos)
      const usados = D.certidoes.flatMap(c => [c].concat(c.historico || [])).map(mesDe).concat(arqs.map(a => a.mes)).filter(m => m <= atual);
      const meses = []; for (let m = usados.reduce((x, y) => (y < x ? y : x), atual); m <= atual;) { meses.unshift(m); const [y, mm] = m.split('-').map(Number); m = mm === 12 ? `${y + 1}-01` : `${y}-${String(mm + 1).padStart(2, '0')}`; }
      const fimMes = m => { const [y, mm] = m.split('-').map(Number); return iso(new Date(y, mm, 0)); };
      // Versão de cada documento que valia na competência: a mais recente guardada até aquele mês
      const vigente = c => [c].concat(c.historico || []).filter(v => mesDe(v) <= M && (v.arquivo || v === c || !real())).sort((x, y) => mesDe(y).localeCompare(mesDe(x)) || String(y.criado || '').localeCompare(String(x.criado || '')))[0];
      const sitMes = v => !v.validade ? { cls: 'enviado', txt: 'sem validade' } : v.validade < M + '-01' ? { cls: 'classificar', txt: `vencida em ${dt(v.validade)}/${v.validade.slice(2, 4)}` }
        : v.validade < fimMes(M) ? { cls: 'pendente', txt: `venceu em ${dt(v.validade)}` } : { cls: 'enviado', txt: 'válida no mês' };
      const ver = x => real() && x.arquivo ? `<button class="link" data-ver="${esc(x.arquivo)}">ver</button>` : '';
      const hist = c => { const hs = (c.historico || []).filter(h => h.arquivo || !real()); return hs.length ? `<details class="hist"><summary>${hs.length} cópia(s) anteriores</summary>${[...hs].sort((x, y) => mesDe(y).localeCompare(mesDe(x))).map(h => `<div class="muted">${nomeMes(mesDe(h))} · ${h.validade ? 'válida até ' + dt(h.validade) + '/' + h.validade.slice(2, 4) : 'sem validade'}${h.arquivo ? ` · ${ver(h)}` : ''}</div>`).join('')}</details>` : ''; };
      const linhasAgora = [...D.certidoes].sort((a, b) => (a.validade || '9').localeCompare(b.validade || '9')).map(c => `<tr><td><strong>${esc(c.nome)}</strong>${c.numero ? `<div class="muted">${esc(c.numero)}</div>` : ''}${c.internas ? `<div class="muted">certificado ${sitData(c.validade).txt}</div>` : ''}
            ${!c.semArquivo && mesDe(c) < atual ? `<div class="muted">cópia guardada em ${nomeMes(mesDe(c))}</div>` : ''}${hist(c)}</td>
          <td class="num"><span class="tag ${situacao(c.nome).cls}">${situacao(c.nome).txt}</span><div><button class="link" data-up="${esc(c.nome)}">atualizar</button>${ver(c) ? ' · ' + ver(c) : ''}</div></td></tr>
          ${(c.internas || []).map(i => `<tr class="sub-row"><td>↳ ${esc(i.nome)}</td><td class="num"><span class="tag ${sitData(i.validade).cls}">${sitData(i.validade).txt}</span><div><button class="link" data-up="${esc(c.nome)}|${esc(i.nome)}">atualizar</button></div></td></tr>`).join('')}`).join('');
      const linhasMes = D.certidoes.map(c => { const v = vigente(c);
        return `<tr><td><strong>${esc(c.nome)}</strong><div class="muted">${v ? `cópia de ${nomeMes(mesDe(v))}${v.validade ? ' · válida até ' + dt(v.validade) + '/' + v.validade.slice(2, 4) : ''}` : 'nenhuma cópia guardada até este mês'}</div></td>
          <td class="num">${v ? `<span class="tag ${sitMes(v).cls}">${sitMes(v).txt}</span>` : '<span class="tag classificar">falta</span>'}<div>${v && ver(v) ? ver(v) + ' · ' : ''}<button class="link" data-up="${esc(c.nome)}" data-comp="${M}">guardar cópia de ${nomeMes(M)}</button></div></td></tr>`; }).join('');
      // NFs por cliente; prints por cliente e, dentro dele, por PI
      const doMes = tipo => arqs.filter(a => a.tipo === tipo && a.mes === M);
      const grupos = l => [...new Set(l.map(a => a.pi.orgao))].sort().map(o => [o, l.filter(a => a.pi.orgao === o)]);
      const item = a => `<li class="todo"><div>${esc(a.nome)}<div class="muted">PI ${esc(a.pi.numero)} · ${esc(a.pi.cliente)}</div></div>${ver(a)}</li>`;
      const nfs = doMes('nf'), prints = doMes('print'), avulsos = doMes('avulso');
      const vazio = `<p class="muted">Nada em ${nomeMes(M)}. NFs e prints entram pela tela de cada PI, no mês em que são anexados.</p>`;
      const blocoNf = nfs.length ? grupos(nfs).map(([o, l]) => `<p style="margin:12px 0 4px"><strong>${esc(o)}</strong> <span class="muted">(${l.length})</span></p><ul class="alerts">${l.map(item).join('')}</ul>`).join('') : vazio;
      const blocoPr = prints.length ? grupos(prints).map(([o, l]) => `<p style="margin:12px 0 4px"><strong>${esc(o)}</strong> <span class="muted">(${l.length})</span></p>${[...new Set(l.map(a => a.pi.numero))].map(n => { const da = l.filter(a => a.pi.numero === n);
          return `<details class="hist"><summary>PI ${esc(n)} · ${esc(da[0].pi.cliente)} · ${da.length} print(s)</summary><ul class="alerts">${da.map(a => `<li class="todo"><div>${esc(a.nome)}</div>${ver(a)}</li>`).join('')}</ul></details>`; }).join('')}`).join('') : vazio;
      return `<h1>Arquivo da empresa</h1><p class="sub">Cada mês-competência guarda a sua cópia de cada documento. Escolha o mês para ver as cópias de meses anteriores.</p>
      <div class="card form" style="margin-bottom:12px"><label>Competência<select id="arq-mes">${meses.map(m => `<option value="${m}" ${m === M ? 'selected' : ''}>${nomeMes(m)}${m === atual ? ' (mês atual)' : ''}</option>`).join('')}</select></label>
        <p class="muted" style="margin:0">${nomeMes(M)}: ${D.certidoes.filter(c => agora ? !c.semArquivo : vigente(c)).length} de ${D.certidoes.length} documentos com cópia · ${nfs.length} NF(s) · ${prints.length} print(s)</p></div>
      <div id="up-form"></div>
      <div class="card" style="margin-bottom:12px"><strong>Certidões e registros · ${nomeMes(M)}</strong><table>${agora ? linhasAgora : linhasMes}</table>
        ${agora ? `<p class="muted">O certificado de registro (CERCA, CRC) tem validade própria, mas cada certidão listada nele vence antes. Certidão interna vencida precisa ir anexada atualizada junto com o certificado.</p>
        ${real() ? '<div class="form inline"><input id="td-nome" placeholder="Novo tipo de documento (ex.: Alvará)"><button id="td-ok">Adicionar</button></div>' : ''}` : `<p class="muted">Mostra a cópia que valia em ${nomeMes(M)}. Se faltar a do mês, guarde-a aqui; ela entra no histórico sem mudar a versão atual.</p>`}</div>
      <details class="card" style="margin-bottom:12px" open><summary><strong>Notas fiscais por cliente · ${nomeMes(M)} (${nfs.length})</strong></summary>${blocoNf}</details>
      <details class="card" style="margin-bottom:12px"${prints.length ? ' open' : ''}><summary><strong>Prints de veiculação por cliente e PI · ${nomeMes(M)} (${prints.length})</strong></summary>${blocoPr}</details>
      ${avulsos.length ? `<details class="card"><summary><strong>Outros anexos de PI · ${nomeMes(M)} (${avulsos.length})</strong></summary><ul class="alerts">${avulsos.map(item).join('')}</ul></details>` : ''}`;
    },
    cadastros() {
      // Todos os documentos do Arquivo numa lista só; o certificado de registro (CERCA, CRC) é um deles, marcado como tal
      const docsLib = [...D.certidoes.map(c => c.nome)].sort((x, y) => (ehRegistro(y) - ehRegistro(x)) || x.localeCompare(y));
      const dis = real() ? '' : 'disabled';
      const formOrg = o => { const k = o ? o.id || o.nome : 'novo', sel = o ? o.extras.concat(registrosDe(o)) : D.padrao;
        return `<label>Nome<input id="og-nome-${esc(k)}" value="${esc(o ? o.nome : '')}" placeholder="ex.: Prefeitura de Dourados"></label>
        <label class="check"><input type="radio" name="og-modo-${esc(k)}" value="lista" ${!o || o.mapeado ? 'checked' : ''}> Enviar só os documentos marcados</label>
        <label class="check"><input type="radio" name="og-modo-${esc(k)}" value="tudo" ${o && !o.mapeado ? 'checked' : ''}> Ainda não sei: enviar todas as certidões, mais o certificado de registro marcado</label>
        <p style="margin:12px 0 4px"><strong>Documentos exigidos</strong></p>
        <div class="docs-grid">${docsLib.map(n => `<label class="check"><input type="checkbox" data-og="${esc(k)}" value="${esc(n)}" ${sel.includes(n) ? 'checked' : ''}> ${esc(n)}${ehRegistro(n) ? ' <span class="muted">(certificado de registro)</span>' : ''}</label>`).join('')}</div>
        <div class="btns"><button class="primary" data-og-save="${esc(k)}" ${o && o.id ? `data-id="${o.id}"` : ''} ${dis}>Guardar</button>${o && o.id ? `<button class="link perigo" data-og-del="${o.id}" ${dis}>excluir</button>` : ''}</div>`; };
      const formAg = a => { const k = a ? a.id || a.nome : 'nova';
        return `<label>Nome<input id="ag-nome-${esc(k)}" value="${esc(a ? a.nome : '')}" placeholder="ex.: Agência X"></label>
        <label>E-mail padrão (vale para todos os clientes sem contato próprio)<input type="email" id="ag-email-${esc(k)}" value="${esc(a ? a.padrao : '')}" placeholder="ex.: midia@agencia.com.br"></label>
        <div class="btns"><button class="primary" data-ag-save="${esc(k)}" ${a && a.id ? `data-id="${a.id}"` : ''} ${dis}>Guardar</button>${a && a.id ? `<button class="link perigo" data-ag-del="${a.id}" ${dis}>excluir</button>` : ''}</div>
        ${a ? `<p style="margin:16px 0 4px"><strong>Contato por cliente</strong></p><p class="muted" style="margin:0 0 8px">Quando a agência tem um atendente para um cliente, o e-mail da PI vai para ele.</p>
          <ul class="alerts">${a.atendentes.map(t => `<li class="todo"><div>${esc(t.cliente)}<div class="muted">${esc(t.nome || '')} ${esc(t.email)}</div></div>${real() && t.id ? `<button class="link perigo" data-at-del="${t.id}">remover</button>` : ''}</li>`).join('') || '<li class="muted">Nenhum: tudo vai para o e-mail padrão.</li>'}</ul>
          ${real() && a.id ? `<div class="form"><label>Cliente<select id="at-org-${a.id}">${D.orgaos.map(o => `<option value="${o.id}">${esc(o.nome)}</option>`).join('')}</select></label><label>Nome do atendente<input id="at-nome-${a.id}"></label><label>E-mail<input type="email" id="at-email-${a.id}"></label><div class="btns"><button data-at-add="${a.id}">+ Adicionar contato</button></div></div>` : ''}` : ''}`; };
      return `<h1>Cadastros</h1><p class="sub">A base de tudo: quem são os clientes, o que cada um exige e para qual e-mail vai cada processo.</p>
      <h2 class="etapa">Clientes (órgãos)</h2>
      <p class="muted" style="margin-top:0">CERCA e CRC são um documento só: o certificado de registro cadastral que o órgão emite depois de conferir um conjunto de certidões. Por isso aparece aqui como um dos documentos exigidos; as certidões que ele lista, com vencimentos próprios, ficam no Arquivo, dentro dele.</p>
      ${D.orgaos.map(o => `<details class="card form" style="margin-bottom:8px"><summary><strong>${esc(o.nome)}</strong> <span class="tag ${o.mapeado ? 'enviado' : 'pendente'}">${o.mapeado ? `${exigidos(o.nome).length} docs exigidos` : 'envia tudo'}</span></summary>${formOrg(o)}</details>`).join('')}
      <details class="card form" style="margin-bottom:8px"><summary><strong>+ Novo cliente</strong></summary>${formOrg(null)}</details>
      <h2 class="etapa">Agências</h2>
      ${D.agencias.map(a => `<details class="card form" style="margin-bottom:8px"><summary><strong>${esc(a.nome)}</strong> <span class="muted">${esc(a.padrao || 'sem e-mail')}</span>${manualDe(a.nome, '') || D.manuais.some(m => m.agencia === a.nome) ? ' <span class="tag enviado">manual</span>' : ''}</summary>${formAg(a)}</details>`).join('')}
      <details class="card form"><summary><strong>+ Nova agência</strong></summary>${formAg(null)}</details>`;
    },
    resumo() {
      const msg = textoResumo();
      return `<p><a href="#painel">← Painel</a></p><h1>Resumo do dia</h1><p class="sub">Prévia da mensagem. O envio automático todo dia de manhã vem numa próxima etapa.</p>
      <div class="phone"><div class="bubble">${esc(msg).replace(/\*(.+?)\*/g, '<strong>$1</strong>')}</div></div>
      <div class="btns" style="justify-content:center"><a class="btn primary" href="https://wa.me/?text=${encodeURIComponent(msg)}" target="_blank" rel="noopener">Mandar no WhatsApp</a></div>`;
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
    const ex = document.getElementById('pi-excluir');
    if (ex) ex.addEventListener('click', () => {
      // Dois toques: o primeiro pede confirmação, sem janela do navegador
      if (!ex.dataset.conf) { ex.dataset.conf = '1'; ex.textContent = 'Toque de novo para excluir a PI e os arquivos dela'; setTimeout(() => { if (ex.isConnected) { delete ex.dataset.conf; ex.textContent = 'Excluir esta PI'; } }, 5000); return; }
      const pi = piAtual();
      acao(() => N.acoes.excluirPi(pi.id), `PI ${pi.numero} excluída.`).then(() => { location.hash = 'pis'; });
    });
    document.querySelectorAll('button[data-up]').forEach(btn => btn.addEventListener('click', () => {
      const [c, i] = btn.dataset.up.split('|');
      document.getElementById('up-form').innerHTML = `<div class="card form" style="margin-bottom:12px"><strong>Atualizar: ${esc(i || c)}</strong>
        <label>Arquivo (PDF ou foto)<input type="file" id="up-f" accept="application/pdf,image/*"></label>
        <label>Válido até<input type="date" id="up-d"></label>
        <label>Competência (mês a que a cópia pertence)<input type="month" id="up-m" value="${btn.dataset.comp || iso(today).slice(0, 7)}" max="${iso(today).slice(0, 7)}"></label>
        <div class="btns"><button class="primary" id="up-ok">Guardar</button><button id="up-x">Cancelar</button></div>
        <p class="muted">${real() ? 'O arquivo vai para o armazenamento privado da empresa. A versão anterior fica guardada.' : 'Demonstração: o arquivo fica só neste aparelho. Na versão final, vai para o armazenamento da plataforma, com login.'}</p></div>`;
      window.scrollTo(0, 0);
      document.getElementById('up-x').onclick = () => { document.getElementById('up-form').innerHTML = ''; };
      document.getElementById('up-ok').onclick = () => {
        const v = document.getElementById('up-d').value, f = document.getElementById('up-f').files[0];
        if (!v && !f) { document.getElementById('up-d').focus(); return; }
        const alvo = cert(c);
        const comp = (document.getElementById('up-m').value || iso(today).slice(0, 7)) + '-01', antiga = !i && comp.slice(0, 7) < mesDe(alvo) && !alvo.semArquivo;
        if (real()) { acao(() => N.acoes.atualizarDocumento(alvo, i, f, v || null, comp), antiga ? `Cópia de ${nomeMes(comp.slice(0, 7))} guardada no histórico.` : 'Documento atualizado.'); return; }
        if (antiga) { (alvo.historico = alvo.historico || []).push({ nome: alvo.nome, validade: v || null, competencia: comp }); render(); return; }
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
    document.querySelectorAll('button[data-nc]').forEach(b => b.addEventListener('click', () => {
      const rec = b.dataset.nc === 'receber';
      document.querySelectorAll('button[data-nc]').forEach(x => x.classList.toggle('on', x === b));
      document.getElementById('nc-tipo').value = b.dataset.nc;
      document.getElementById('nc-l1').textContent = rec ? 'De quem (cliente ou agência)' : 'Descrição';
      document.getElementById('nc-desc').placeholder = rec ? 'ex.: Agência X' : 'ex.: Aluguel';
      document.getElementById('nc-l2').textContent = rec ? 'Referência (opcional)' : 'Observação (opcional)';
      document.getElementById('nc-ref').placeholder = rec ? 'ex.: PI 58820' : 'ex.: fornecedor, nº do boleto';
    }));
    // Conciliação
    const extDe = id => (D.extrato || []).find(x => x.id === id);
    document.querySelectorAll('button[data-conc]').forEach(b => b.addEventListener('click', () => { const [x, c] = b.dataset.conc.split('|'); acao(() => N.acoes.conciliar(extDe(x), c), 'Conciliado: a conta foi dada como quitada.'); }));
    document.querySelectorAll('button[data-lanc]').forEach(b => b.addEventListener('click', () => acao(() => N.acoes.lancarDoExtrato(extDe(b.dataset.lanc)), 'Lançado como conta quitada.')));
    document.querySelectorAll('button[data-ign]').forEach(b => b.addEventListener('click', () => acao(() => N.acoes.ignorarExtrato(b.dataset.ign), 'Ignorado.')));
    // Cadastros
    const val = id => { const e = document.getElementById(id); return e ? e.value.trim() : ''; };
    document.querySelectorAll('button[data-og-save]').forEach(b => b.addEventListener('click', () => {
      const k = b.dataset.ogSave, nome = val('og-nome-' + k); if (!nome) { avisar('Informe o nome do cliente.', 'bad'); return; }
      const modo = (document.querySelector(`input[name="og-modo-${CSS.escape(k)}"]:checked`) || {}).value;
      const extras = [...document.querySelectorAll(`input[data-og="${CSS.escape(k)}"]:checked`)].map(i => i.value);
      acao(() => N.acoes.salvarOrgao({ id: b.dataset.id, nome, registro: extras.find(ehRegistro) || null, extras, mapeado: modo === 'lista' }), 'Cliente guardado.');
    }));
    document.querySelectorAll('button[data-og-del]').forEach(b => b.addEventListener('click', () => {
      if (!b.dataset.conf) { b.dataset.conf = 1; b.textContent = 'toque de novo para excluir'; return; }
      acao(() => N.acoes.excluirOrgao(b.dataset.ogDel), 'Cliente excluído.');
    }));
    document.querySelectorAll('button[data-ag-save]').forEach(b => b.addEventListener('click', () => {
      const k = b.dataset.agSave, nome = val('ag-nome-' + k); if (!nome) { avisar('Informe o nome da agência.', 'bad'); return; }
      acao(() => N.acoes.salvarAgencia({ id: b.dataset.id, nome, email: val('ag-email-' + k) }), 'Agência guardada.');
    }));
    document.querySelectorAll('button[data-ag-del]').forEach(b => b.addEventListener('click', () => {
      if (!b.dataset.conf) { b.dataset.conf = 1; b.textContent = 'toque de novo para excluir'; return; }
      acao(() => N.acoes.excluirAgencia(b.dataset.agDel), 'Agência excluída.');
    }));
    document.querySelectorAll('button[data-at-add]').forEach(b => b.addEventListener('click', () => {
      const a = b.dataset.atAdd, email = val('at-email-' + a); if (!email) { avisar('Informe o e-mail do contato.', 'bad'); return; }
      acao(() => N.acoes.salvarAtendente({ agencia: a, orgao: val('at-org-' + a), nome: val('at-nome-' + a), email }), 'Contato adicionado.');
    }));
    document.querySelectorAll('button[data-at-del]').forEach(b => b.addEventListener('click', () => acao(() => N.acoes.excluirAtendente(b.dataset.atDel), 'Contato removido.')));
    const am = document.getElementById('arq-mes');
    if (am) am.addEventListener('change', () => { mesArq = am.value; render(); });
    const td = document.getElementById('td-ok');
    if (td) td.addEventListener('click', () => { const n = val('td-nome'); if (!n) return; if (cert(n)) { avisar('Esse documento já existe.', 'bad'); return; } acao(() => N.acoes.novoTipoDoc(n), 'Documento adicionado. Toque em "atualizar" para guardar o PDF.'); });
    const nc = document.getElementById('nc-ok');
    if (nc) nc.addEventListener('click', () => {
      const g = id => document.getElementById(id).value.trim();
      const valor = valorBR(g('nc-valor')), venc = g('nc-venc'), desc = g('nc-desc');
      if (!desc || !venc || !(valor > 0)) { avisar('Preencha os campos, o vencimento e o valor.', 'bad'); return; }
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
    let [route, sel] = decodeURIComponent(location.hash.slice(1)).split('/');
    route = { bancos: 'contas', financeiro: 'contas', documentos: 'arquivo', envios: 'pis', inicio: 'rotinas', hoje: 'rotinas' }[route] || route;
    const r = views[route] && route !== 'novaPi' ? route : 'rotinas';
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
      <p class="muted" style="margin-top:16px"><a href="#rotinas" id="demo">Ver a demonstração</a></p></div>`;
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
