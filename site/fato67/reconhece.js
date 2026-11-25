// Reconhecimento de documentos sem IA: frases fixas do texto do PDF, linha digitável e regras aprendidas.
// Entrada: { de, assunto, nome, texto }. Saída: sugestão de destino e os dados lidos.
(function (raiz) {
  const sem = s => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const dataIso = s => { const m = String(s).match(/(\d{2})\/(\d{2})\/(\d{4})/); return m ? `${m[3]}-${m[2]}-${m[1]}` : null; };
  const num = s => { const t = String(s).replace(/[^\d.,]/g, ''); return t ? parseFloat(t.replace(/\./g, '').replace(',', '.')) : NaN; };

  // Certidões e registros: padrão no texto → palavras para achar o tipo já cadastrado na empresa
  const CERTIDOES = [
    { re: /debitos trabalhistas|cndt\b/, chaves: ['trabalhista'], nome: 'CND Trabalhista (TST)' },
    { re: /regularidade do fgts|certificado de regularidade|\bcrf\b/, chaves: ['fgts', 'crf'], nome: 'CRF do FGTS' },
    { re: /tributos federais|divida ativa da uniao/, chaves: ['federal'], nome: 'CND Federal (Receita e PGFN)' },
    { re: /falencia|concordata|recuperacao judicial/, chaves: ['falencia'], nome: 'Certidão de falência e concordata' },
    { re: /certificado de registro cadastral|\bcerca\b/, chaves: ['cerca', 'crc', 'registro'], nome: 'Certificado de registro cadastral' },
    { re: /optante pelo simples|consulta optantes/, chaves: ['simples'], nome: 'Comprovante de inscrição no Simples' },
    { re: /certidao.{0,80}(estadual|secretaria de estado de fazenda|sefaz)|(sefaz|fazenda estadual).{0,200}certidao/, chaves: ['estadual'], nome: 'CND Estadual' },
    { re: /certidao.{0,80}(municipal|municipio|prefeitura)|(prefeitura|municipio).{0,200}certidao/, chaves: ['municipal'], nome: 'CND Municipal' }
  ];

  // Linha digitável de boleto bancário (47 dígitos) ou de arrecadação (48 dígitos, começa com 8: DAS, guias)
  function linhaDigitavel(texto) {
    const t = String(texto || '');
    const boleto = t.match(/\b(\d{5})[.\s]?(\d{5})\s+(\d{5})[.\s]?(\d{6})\s+(\d{5})[.\s]?(\d{6})\s+(\d)\s+(\d{14})\b/);
    if (boleto) {
      const d = boleto.slice(1).join(''), fator = +d.slice(33, 37), valor = +d.slice(37) / 100;
      // Fator de vencimento: reiniciou em 22/02/2025 (fator 1000)
      let venc = null;
      if (fator >= 1000) { const x = new Date(Date.UTC(2025, 1, 22)); x.setUTCDate(x.getUTCDate() + fator - 1000); venc = x.toISOString().slice(0, 10); }
      return { linha: d, valor: valor || null, vencimento: venc, tipo: 'boleto' };
    }
    const arr = t.match(/\b(8\d{10})[\s-]?(\d)\s+(\d{11})[\s-]?(\d)\s+(\d{11})[\s-]?(\d)\s+(\d{11})[\s-]?(\d)\b/);
    if (arr) {
      const cod = arr[1] + arr[3] + arr[5] + arr[7];   // código de barras sem os dígitos verificadores
      const real = /[68]/.test(cod[2]);                // 3º dígito 6 ou 8: valor em reais
      return { linha: arr.slice(1).join(''), valor: real ? +cod.slice(4, 15) / 100 || null : null, vencimento: null, tipo: 'arrecadacao' };
    }
    return null;
  }

  function validade(t) {
    const m = t.match(/(?:valid[ao]s?\s+ate|validade|valida\s+por\s+\d+\s+dias.{0,40}?ate)\W{0,12}(\d{2}\/\d{2}\/\d{4})(?:\s*(?:a|ate)\s*(\d{2}\/\d{2}\/\d{4}))?/);
    return m ? dataIso(m[2] || m[1]) : null;
  }
  function vencimento(t) {
    const m = t.match(/(?:vencimento|pagar este documento ate|data de vencimento|vence em)\W{0,15}(\d{2}\/\d{2}\/\d{4})/);
    return m ? dataIso(m[1]) : null;
  }
  function valor(t) {
    const m = t.match(/(?:valor total do documento|valor do documento|valor cobrado|valor a pagar|total a pagar)\W{0,15}(?:r\$\s*)?(\d{1,3}(?:\.\d{3})*,\d{2})/);
    return m ? num(m[1]) : null;
  }
  const remetente = de => { const m = sem(de).match(/[\w.+-]+@[\w.-]+/); return m ? m[0] : sem(de).trim(); };
  const casaRegra = (r, e) => r.campo === 'remetente' ? remetente(e.de) && remetente(e.de).includes(sem(r.padrao))
    : r.campo === 'arquivo' ? sem(e.nome).includes(sem(r.padrao)) : sem(e.texto).includes(sem(r.padrao));

  // tipos: nomes de documentos já cadastrados na empresa (para casar "CND Trabalhista" com o nome que eles usam)
  function analisar(e, regras, tipos) {
    const t = sem([e.assunto, e.nome, e.texto].join(' \n ')).replace(/\s+/g, ' ');
    const out = { sugestao: null, tipo: null, validade: null, valor: null, vencimento: null, linha: null, categoria: null, descricao: null, motivo: '', regra: null };
    const ld = linhaDigitavel(e.texto);
    if (ld) { out.linha = ld.linha; out.valor = ld.valor; out.vencimento = ld.vencimento; }
    out.valor = out.valor || valor(t); out.vencimento = out.vencimento || vencimento(t);
    const lista = (tipos || []).map(n => ({ n, s: sem(n) }));
    const c = CERTIDOES.find(x => x.re.test(t));
    if (/documento de arrecadacao do simples nacional|\bdas\b.{0,40}simples/.test(t)) {
      Object.assign(out, { sugestao: 'pagar', categoria: 'Impostos', descricao: 'DAS Simples Nacional', motivo: 'DAS do Simples Nacional' });
    } else if (c) {
      const achado = lista.find(x => c.chaves.some(k => x.s.includes(k)));
      Object.assign(out, { sugestao: 'documento', tipo: achado ? achado.n : c.nome, validade: validade(t), motivo: achado ? achado.n : c.nome });
    } else if (/nota fiscal|nfs-?e|danfe/.test(t)) {
      Object.assign(out, { sugestao: 'documento', tipo: 'Nota fiscal', motivo: 'Nota fiscal' });
    } else if (ld || /boleto|cobranca|fatura|honorarios/.test(t)) {
      Object.assign(out, { sugestao: 'pagar', categoria: /honorario/.test(t) ? 'Honorários' : 'A classificar', descricao: e.assunto || e.nome || 'Cobrança', motivo: ld ? 'Boleto' : 'Cobrança' });
    }
    // Regra aprendida manda no destino; os dados lidos do PDF continuam valendo
    const r = (regras || []).find(x => casaRegra(x, e));
    if (r) {
      out.regra = r; out.sugestao = r.destino;
      if (r.tipo_doc) out.tipo = r.tipo_doc; if (r.categoria) out.categoria = r.categoria; if (r.descricao && !out.descricao) out.descricao = r.descricao;
      out.motivo = `regra: ${r.padrao}` + (out.motivo ? ` · ${out.motivo}` : '');
    }
    if (!out.sugestao) out.motivo = 'não reconhecido';
    return out;
  }

  // Texto de um PDF (navegador, com pdf.js carregado sob demanda)
  async function textoPdf(buf) {
    const lib = raiz.pdfjsLib; if (!lib) return '';
    const pdf = await lib.getDocument({ data: buf }).promise; let out = '';
    for (let i = 1; i <= Math.min(pdf.numPages, 5); i++) {
      const pg = await pdf.getPage(i), c = await pg.getTextContent();
      out += c.items.map(x => x.str + (x.hasEOL ? '\n' : ' ')).join('') + '\n';
    }
    return out.slice(0, 20000);
  }

  const api = { analisar, linhaDigitavel, remetente, textoPdf, sem };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else raiz.Reconhece = api;
})(typeof window !== 'undefined' ? window : globalThis);
