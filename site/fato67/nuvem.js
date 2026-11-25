// Camada de dados real (Supabase). Monta o mesmo formato dos dados de demonstração,
// para as telas funcionarem igual nos dois modos. Sem login, nada é lido.
(function () {
  const C = window.FATO67_CONFIG;
  if (!C || !window.supabase) return;
  const sb = window.supabase.createClient(C.url, C.chave, { auth: { flowType: 'pkce', persistSession: true, detectSessionInUrl: true } });
  const hoje = () => { const x = new Date(); x.setMinutes(x.getMinutes() - x.getTimezoneOffset()); return x.toISOString().slice(0, 10); };
  const ok = ({ data, error }) => { if (error) throw new Error(error.message); return data; };
  const limpa = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^\w.-]+/g, '_').slice(-80);
  let emp = null, user = null;

  async function sessao() {
    const { data } = await sb.auth.getSession();
    // Depois do login, tira ?code= da barra de endereço
    if (/[?&]code=/.test(location.search)) history.replaceState(null, '', location.pathname + location.hash);
    user = data.session ? data.session.user : null;
    if (user) await sb.rpc('aceitar_convites');
    return user;
  }
  const destino = () => location.origin + location.pathname;
  const entrarGoogle = () => sb.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: destino() } }).then(ok);
  const entrarEmail = email => sb.auth.signInWithOtp({ email, options: { emailRedirectTo: destino() } }).then(ok);
  const sair = () => sb.auth.signOut();

  async function empresas() { return ok(await sb.from('empresas').select('id,nome,token_entrada,docs_padrao,passos_padrao').order('nome')); }

  async function carregar(empresaId) {
    const lista = await empresas();
    if (!lista.length) return null;
    emp = lista.find(e => e.id === empresaId) || lista[0];
    const q = t => sb.from(t).select('*').eq('empresa_id', emp.id);
    let [contas, saldos, docs, orgaos, agencias, pis, pagar, receber, entrada, extrato] = (await Promise.all([
      q('contas_bancarias').order('ordem'), q('saldos').order('data', { ascending: false }).limit(400),
      q('documentos').order('criado_em', { ascending: false }), q('orgaos').order('nome'), q('agencias').order('nome'),
      q('pis').order('data', { ascending: false }), q('contas_pagar'), q('contas_receber').is('recebido_em', null),
      q('entrada').eq('resolvido', false).order('recebido_em', { ascending: false }),
      q('extrato').order('data', { ascending: false }).limit(200)
    ])).map(ok);
    const agIds = agencias.map(a => a.id), piIds = pis.map(p => p.id);
    const [atend, manuais, piArq] = (await Promise.all([
      agIds.length ? sb.from('atendentes').select('*').in('agencia_id', agIds) : { data: [] },
      agIds.length ? sb.from('manuais').select('*').in('agencia_id', agIds) : { data: [] },
      piIds.length ? sb.from('pi_arquivos').select('*').in('pi_id', piIds) : { data: [] }
    ])).map(ok);
    const orgNome = id => (orgaos.find(o => o.id === id) || {}).nome || '—';
    const agNome = id => (agencias.find(a => a.id === id) || {}).nome || '—';
    const ultimo = id => saldos.find(s => s.conta_id === id);
    const doc = d => ({ id: d.id, nome: d.tipo, numero: d.numero, validade: d.validade, arquivo: d.arquivo, semArquivo: !d.arquivo, criado: d.criado_em });
    const todosDocs = docs; docs = docs.filter(d => d.atual);
    return {
      real: true, empresa: emp, empresas: lista, usuario: user,
      saldos: contas.map(c => { const s = ultimo(c.id); return { id: c.id, conta: c.nome, tipo: c.tipo, saldo: s ? +s.saldo : 0, data: s ? s.data : null, origem: s ? s.origem : null }; }),
      certidoes: docs.filter(d => !d.pai_id).map(d => ({ ...doc(d), historico: todosDocs.filter(v => !v.atual && v.tipo === d.tipo && !v.pai_id).map(doc), internas: docs.filter(i => i.pai_id === d.id).map(doc) }))
        .map(c => (c.internas.length ? c : { ...c, internas: undefined })),
      padrao: emp.docs_padrao || [],
      passosPadrao: emp.passos_padrao && emp.passos_padrao.length ? emp.passos_padrao : ['Conferir a PI', 'Emitir a NF', 'Juntar os prints', 'Enviar o processo'],
      orgaos: orgaos.map(o => ({ id: o.id, nome: o.nome, registro: o.registro, extras: o.extras || [], mapeado: o.mapeado })),
      agencias: agencias.map(a => ({ id: a.id, nome: a.nome, padrao: a.email_padrao || '', atendentes: atend.filter(t => t.agencia_id === a.id).map(t => ({ id: t.id, cliente: orgNome(t.orgao_id), nome: t.nome, email: t.email })) })),
      manuais: manuais.map(m => ({ agencia: agNome(m.agencia_id), cliente: orgNome(m.orgao_id), passos: m.passos })),
      pis: pis.map(p => {
        const arq = piArq.filter(a => a.pi_id === p.id), nf = arq.find(a => a.tipo === 'nf');
        return { id: p.id, numero: p.numero, orgao: orgNome(p.orgao_id), cliente: agNome(p.agencia_id), data: p.data,
          pasta: { nf: nf ? nf.nome : null, prints: arq.filter(a => a.tipo === 'print').map(a => a.nome), arquivos: arq },
          avulsos: arq.filter(a => a.tipo === 'avulso').map(a => a.nome),
          status: p.status === 'aberta' ? 'pendente' : 'enviada', sel: p.anexos || undefined, feitos: p.passos_feitos };
      }),
      pagar: pagar.map(p => ({ id: p.id, desc: p.descricao, fornecedor: p.fornecedor || '—', categoria: p.categoria || 'A classificar', venc: p.vencimento, valor: +p.valor, origem: p.origem || 'Manual', status: p.pago_em ? 'pago' : 'pendente' })),
      receber: receber.map(r => ({ id: r.id, cliente: r.cliente, ref: r.referencia || '', venc: r.vencimento, valor: +r.valor })),
      entrada: entrada.map(e => ({ id: e.id, arquivo: e.arquivo ? e.arquivo.split('/').pop().replace(/^[0-9a-f-]{36}-/, '') : (e.assunto || '(sem anexo)'), de: e.de || '—', parece: [e.tipo, e.motivo].filter(Boolean).join(' · ') || 'a classificar' })),
      extrato: extrato.map(x => ({ id: x.id, conta_id: x.conta_id, data: x.data, valor: +x.valor, descricao: x.descricao, conciliado: x.conciliado, pagar: x.conta_pagar_id, receber: x.conta_receber_id })),
      whatsappExemplo: ''
    };
  }

  async function subir(pasta, file) {
    const caminho = `${emp.id}/${pasta}/${crypto.randomUUID()}-${limpa(file.name)}`;
    ok(await sb.storage.from('arquivos').upload(caminho, file, { contentType: file.type || 'application/octet-stream' }));
    return caminho;
  }
  const baixar = async caminho => ok(await sb.storage.from('arquivos').download(caminho));

  const acoes = {
    async salvarContas(lista) {
      ok(await sb.from('contas_pagar').insert(lista.map(p => ({ empresa_id: emp.id, descricao: p.desc, categoria: p.categoria, vencimento: p.venc, valor: p.valor, origem: p.origem }))));
    },
    async novaConta({ desc, venc, valor, categoria }) {
      ok(await sb.from('contas_pagar').insert({ empresa_id: emp.id, descricao: desc, vencimento: venc, valor, categoria, origem: 'Manual' }));
    },
    async marcarPaga(id) { ok(await sb.from('contas_pagar').update({ pago_em: hoje() }).eq('id', id)); },
    async novoReceber({ cliente, ref, venc, valor }) {
      ok(await sb.from('contas_receber').insert({ empresa_id: emp.id, cliente, referencia: ref, vencimento: venc, valor }));
    },
    async marcarRecebido(id) { ok(await sb.from('contas_receber').update({ recebido_em: hoje() }).eq('id', id)); },
    async criarPi({ numero, orgao, agencia, anexos }) {
      return ok(await sb.from('pis').insert({ empresa_id: emp.id, numero, orgao_id: orgao, agencia_id: agencia, anexos }).select('id').single());
    },
    async anexosPi(id, anexos) { ok(await sb.from('pis').update({ anexos }).eq('id', id)); },
    async passosPi(id, n) { ok(await sb.from('pis').update({ passos_feitos: n }).eq('id', id)); },
    // Exclui a PI, seus registros de arquivo e os arquivos guardados no Storage
    async excluirPi(id) {
      const arqs = ok(await sb.from('pi_arquivos').select('arquivo').eq('pi_id', id));
      if (arqs.length) ok(await sb.storage.from('arquivos').remove(arqs.map(a => a.arquivo)));
      ok(await sb.from('contas_receber').update({ pi_id: null }).eq('pi_id', id));
      ok(await sb.from('pis').delete().eq('id', id));
    },
    async statusPi(id, status) { ok(await sb.from('pis').update({ status }).eq('id', id)); },
    async arquivoPi(id, tipo, file) {
      const arquivo = await subir('pis', file);
      ok(await sb.from('pi_arquivos').insert({ pi_id: id, tipo, nome: file.name, arquivo }));
    },
    // Nova versão de documento: guarda o arquivo, cria a versão e aposenta a anterior
    async atualizarDocumento(c, interna, file, validade) {
      const velho = interna ? (c.internas || []).find(i => i.nome === interna) : c;
      const arquivo = file ? await subir('documentos', file) : (velho && velho.arquivo) || null;
      const novo = ok(await sb.from('documentos').insert({ empresa_id: emp.id, tipo: interna || c.nome, numero: velho && velho.numero, validade, arquivo, pai_id: interna ? c.id : null, origem: 'upload' }).select('id').single());
      if (velho && velho.id) {
        ok(await sb.from('documentos').update({ atual: false }).eq('id', velho.id));
        if (!interna) ok(await sb.from('documentos').update({ pai_id: novo.id }).eq('pai_id', velho.id).eq('atual', true));
      }
    },
    async resolverEntrada(id) { ok(await sb.from('entrada').update({ resolvido: true }).eq('id', id)); },
    async saldo(conta, valor, data) {
      ok(await sb.from('saldos').upsert({ empresa_id: emp.id, conta_id: conta, data: data || hoje(), saldo: valor, origem: 'manual' }));
    },
    async importarExtrato(conta, r) {
      const linhas = r.lancamentos.map(l => ({ empresa_id: emp.id, conta_id: conta, data: l.data, valor: l.valor, descricao: l.descricao, chave: l.chave, origem: r.origem }));
      let novos = 0;
      for (let i = 0; i < linhas.length; i += 500) {
        novos += ok(await sb.from('extrato').upsert(linhas.slice(i, i + 500), { onConflict: 'conta_id,chave', ignoreDuplicates: true }).select('id')).length;
      }
      if (r.saldo) ok(await sb.from('saldos').upsert({ empresa_id: emp.id, conta_id: conta, data: r.saldo.data, saldo: r.saldo.valor, origem: r.origem }));
      return novos;
    },
    // ---- cadastros ----
    async salvarOrgao(o) {
      const linha = { empresa_id: emp.id, nome: o.nome, registro: o.registro || null, extras: o.extras || [], mapeado: !!o.mapeado };
      ok(o.id ? await sb.from('orgaos').update(linha).eq('id', o.id) : await sb.from('orgaos').insert(linha));
    },
    async excluirOrgao(id) { const r = await sb.from('orgaos').delete().eq('id', id); if (r.error) throw new Error(/foreign key/i.test(r.error.message) ? 'este cliente tem PIs; não dá para excluir' : r.error.message); },
    async salvarAgencia(a) {
      const linha = { empresa_id: emp.id, nome: a.nome, email_padrao: a.email || null };
      ok(a.id ? await sb.from('agencias').update(linha).eq('id', a.id) : await sb.from('agencias').insert(linha));
    },
    async excluirAgencia(id) { const r = await sb.from('agencias').delete().eq('id', id); if (r.error) throw new Error(/foreign key/i.test(r.error.message) ? 'esta agência tem PIs; não dá para excluir' : r.error.message); },
    async salvarAtendente(t) { ok(await sb.from('atendentes').insert({ agencia_id: t.agencia, orgao_id: t.orgao, nome: t.nome || null, email: t.email })); },
    async excluirAtendente(id) { ok(await sb.from('atendentes').delete().eq('id', id)); },
    async docsPadrao(lista) { ok(await sb.from('empresas').update({ docs_padrao: lista }).eq('id', emp.id)); },
    async novoTipoDoc(tipo) { ok(await sb.from('documentos').insert({ empresa_id: emp.id, tipo, origem: 'cadastro' })); },
    // ---- conciliação ----
    async conciliar(x, conta) {
      if (x.valor < 0) {
        ok(await sb.from('contas_pagar').update({ pago_em: x.data }).eq('id', conta));
        ok(await sb.from('extrato').update({ conciliado: true, conta_pagar_id: conta }).eq('id', x.id));
      } else {
        ok(await sb.from('contas_receber').update({ recebido_em: x.data }).eq('id', conta));
        ok(await sb.from('extrato').update({ conciliado: true, conta_receber_id: conta }).eq('id', x.id));
      }
    },
    // Lançamento do extrato sem conta correspondente: cria a conta já quitada e liga
    async lancarDoExtrato(x) {
      if (x.valor < 0) {
        const c = ok(await sb.from('contas_pagar').insert({ empresa_id: emp.id, descricao: x.descricao || 'Saída do extrato', vencimento: x.data, valor: -x.valor, pago_em: x.data, origem: 'Extrato', categoria: 'A classificar' }).select('id').single());
        ok(await sb.from('extrato').update({ conciliado: true, conta_pagar_id: c.id }).eq('id', x.id));
      } else {
        const c = ok(await sb.from('contas_receber').insert({ empresa_id: emp.id, cliente: x.descricao || 'Entrada do extrato', vencimento: x.data, valor: x.valor, recebido_em: x.data }).select('id').single());
        ok(await sb.from('extrato').update({ conciliado: true, conta_receber_id: c.id }).eq('id', x.id));
      }
    },
    async ignorarExtrato(id) { ok(await sb.from('extrato').update({ conciliado: true }).eq('id', id)); },
    async convidar(email, papel) { ok(await sb.from('convites').upsert({ email: email.trim().toLowerCase(), empresa_id: emp.id, papel })); }
  };

  window.Nuvem = { sb, sessao, entrarGoogle, entrarEmail, sair, carregar, baixar, acoes, hoje };
})();
