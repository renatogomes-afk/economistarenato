// Leitura de extratos bancários sem IA: OFX (C6, BB, Mercado Pago exportam) e CSV genérico.
// Devolve { lancamentos: [{ data, valor, descricao, chave }], saldo: { data, valor } | null, erro }
(function (root) {
  const num = s => {
    s = String(s).trim().replace(/R\$\s*/i, '').replace(/\s/g, '');
    if (!s) return NaN;
    let neg = /^\(.*\)$/.test(s) || /-$/.test(s) || /D$/i.test(s); // (12,00), 12,00-, 12,00 D
    s = s.replace(/[()]/g, '').replace(/[-+]$/, '').replace(/[CD]$/i, '');
    if (s.startsWith('-')) { neg = true; s = s.slice(1); } else if (s.startsWith('+')) s = s.slice(1);
    const lc = s.lastIndexOf(','), ld = s.lastIndexOf('.');
    if (lc > ld) s = s.replace(/\./g, '').replace(',', '.');       // 1.234,56
    else if (ld > lc && lc >= 0) s = s.replace(/,/g, '');         // 1,234.56
    const v = parseFloat(s);
    return neg ? -v : v;
  };
  const dataIso = s => {
    s = String(s).trim();
    let m = s.match(/^(\d{4})-?(\d{2})-?(\d{2})/);
    if (m) return `${m[1]}-${m[2]}-${m[3]}`;
    m = s.match(/^(\d{1,2})[\/.-](\d{1,2})[\/.-](\d{2,4})/);
    if (m) return `${m[3].length === 2 ? '20' + m[3] : m[3]}-${m[2].padStart(2, '0')}-${m[1].padStart(2, '0')}`;
    return null;
  };

  // Chave estável para não duplicar ao importar de novo: o mesmo lançamento repetido no dia ganha #2, #3...
  const contador = () => { const n = {}; return k => { n[k] = (n[k] || 0) + 1; return n[k] > 1 ? `${k}#${n[k]}` : k; }; };

  function ofx(txt) {
    const tag = (bloco, t) => { const m = bloco.match(new RegExp(`<${t}>([^<\\r\\n]*)`, 'i')); return m ? m[1].trim() : ''; };
    const lancamentos = [], vez = contador();
    (txt.match(/<STMTTRN>[\s\S]*?(?=<\/STMTTRN>|<STMTTRN>|<\/BANKTRANLIST>)/gi) || []).forEach((b, i) => {
      const data = dataIso(tag(b, 'DTPOSTED')), valor = num(tag(b, 'TRNAMT'));
      if (!data || isNaN(valor)) return;
      const descricao = [tag(b, 'NAME'), tag(b, 'MEMO')].filter(Boolean).filter((x, j, a) => a.indexOf(x) === j).join(' · ');
      lancamentos.push({ data, valor, descricao, chave: tag(b, 'FITID') || vez(`${data}|${valor.toFixed(2)}|${descricao}`) });
    });
    const lb = (txt.match(/<LEDGERBAL>[\s\S]*?(?=<\/LEDGERBAL>|<AVAILBAL>|<\/STMTRS>)/i) || [''])[0];
    const sv = num(tag(lb, 'BALAMT')), sd = dataIso(tag(lb, 'DTASOF'));
    return { lancamentos, saldo: lb && !isNaN(sv) && sd ? { data: sd, valor: sv } : null };
  }

  function linhasCsv(txt) {
    const linhas = txt.split(/\r?\n/).filter(l => l.trim());
    const amostra = linhas.slice(0, 30).join('\n');
    const sep = [';', '\t', ','].sort((a, b) => amostra.split(b).length - amostra.split(a).length)[0];
    const parse = l => { const out = []; let cur = '', q = false;
      for (const c of l) { if (c === '"') q = !q; else if (c === sep && !q) { out.push(cur.trim()); cur = ''; } else cur += c; }
      out.push(cur.trim()); return out; };
    return linhas.map(parse);
  }

  function csv(txt) {
    const rows = linhasCsv(txt);
    const norm = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
    // Cabeçalho: primeira linha que cita data e valor
    let h = rows.findIndex(r => r.some(c => /data|date/.test(norm(c))) && r.some(c => /valor|amount|quantia|montante|credito|debito/.test(norm(c))));
    let iData, iValor, iDesc, iCred, iDeb, iSaldo;
    if (h >= 0) {
      const cab = rows[h].map(norm), achar = re => cab.findIndex(c => re.test(c));
      iData = achar(/^data|date/); if (iData < 0) iData = achar(/data|date/);
      iCred = achar(/credito|entrada/); iDeb = achar(/debito|saida/);
      iValor = achar(/valor|amount|net_amount|quantia|montante/);
      iSaldo = achar(/saldo|balance/);
      iDesc = achar(/descri|histor|lancamento|memo|transaction_type|detalhe|tipo/);
    } else {
      // Sem cabeçalho: coluna com data, coluna com número, maior texto
      const r = rows.find(r => r.some(c => dataIso(c)) && r.some(c => /\d/.test(c) && !isNaN(num(c)) && !dataIso(c)));
      if (!r) return { lancamentos: [], saldo: null, erro: 'Não achei colunas de data e valor neste arquivo.' };
      iData = r.findIndex(c => dataIso(c));
      iValor = r.findIndex((c, i) => i !== iData && /\d/.test(c) && !isNaN(num(c)) && !dataIso(c));
      iDesc = r.reduce((best, c, i) => (i !== iData && i !== iValor && c.length > (r[best] || '').length ? i : best), -1);
      h = -1;
    }
    const lancamentos = [], vez = contador(); let saldo = null;
    rows.slice(h + 1).forEach((r, i) => {
      const data = dataIso(r[iData] || ''); if (!data) return;
      let valor = iValor >= 0 ? num(r[iValor] || '') : NaN;
      if (isNaN(valor) && (iCred >= 0 || iDeb >= 0)) {
        const c = num(r[iCred] || '0') || 0, d = num(r[iDeb] || '0') || 0;
        valor = c - Math.abs(d);
      }
      if (isNaN(valor) || valor === 0) return;
      const descricao = iDesc >= 0 ? (r[iDesc] || '') : '';
      if (/saldo/i.test(descricao) && !/pix|ted|doc/i.test(descricao)) return; // linha "SALDO DO DIA"
      lancamentos.push({ data, valor, descricao, chave: vez(`${data}|${valor.toFixed(2)}|${descricao}`) });
      if (iSaldo >= 0 && !isNaN(num(r[iSaldo] || ''))) { const s = num(r[iSaldo]); if (!saldo || data >= saldo.data) saldo = { data, valor: s }; }
    });
    return { lancamentos, saldo, erro: lancamentos.length ? null : 'Nenhum lançamento reconhecido.' };
  }

  function lerExtrato(nome, txt) {
    if (/<OFX>|OFXHEADER/i.test(txt) || /\.ofx$/i.test(nome)) { const r = ofx(txt); return { ...r, origem: 'ofx', erro: r.lancamentos.length ? null : 'OFX sem lançamentos.' }; }
    return { ...csv(txt), origem: 'csv' };
  }
  const api = { lerExtrato, num, dataIso };
  if (typeof module !== 'undefined') module.exports = api; else root.Extrato = api;
})(this);
