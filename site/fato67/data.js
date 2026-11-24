// Dados de demonstração. Nenhum dado real da FATO67.
(function () {
  const d = n => { const x = new Date(); x.setHours(0,0,0,0); x.setDate(x.getDate() + n); return x.toISOString().slice(0,10); };
  window.DEMO = {
    saldos: [
      { conta: 'C6 Bank PJ (FATO67)', saldo: 48320.55 },
      { conta: 'Banco do Brasil PF (opcional)', saldo: 6210.00 }
    ],
    clientes: [
      { id: 'alfa', nome: 'Construtora Alfa', servicos: ['Consultoria mensal', 'Projeto de reforma'] },
      { id: 'beta', nome: 'Clínica Beta', servicos: ['Manutenção de sistemas'] },
      { id: 'gama', nome: 'Comércio Gama', servicos: ['Consultoria mensal', 'Treinamento'] }
    ],
    pagar: [
      { id: 1, desc: 'DAS Simples Nacional', fornecedor: 'Escritório de contabilidade', categoria: 'Impostos', venc: d(3), valor: 3870.40, origem: 'Guia recebida por e-mail', status: 'pendente' },
      { id: 2, desc: 'Honorários contábeis', fornecedor: 'Escritório de contabilidade', categoria: 'Honorários', venc: d(5), valor: 1450.00, origem: 'Boleto recebido por e-mail', status: 'pendente' },
      { id: 3, desc: 'Licença de software', fornecedor: 'Fornecedor de software', categoria: 'Fornecedores', venc: d(1), valor: 689.90, origem: 'Boleto recebido por e-mail', status: 'pendente' },
      { id: 4, desc: 'Aluguel do escritório', fornecedor: 'Imobiliária', categoria: 'Despesas fixas', venc: d(8), valor: 4200.00, origem: 'Lançamento recorrente', status: 'pendente' },
      { id: 5, desc: 'Internet e telefone', fornecedor: 'Operadora', categoria: 'Despesas fixas', venc: d(12), valor: 329.90, origem: 'Boleto recebido por e-mail', status: 'pendente' },
      { id: 6, desc: 'Pró-labore', fornecedor: 'Roger', categoria: 'Pessoal', venc: d(15), valor: 6000.00, origem: 'Lançamento recorrente', status: 'pendente' },
      { id: 7, desc: 'Material de escritório', fornecedor: 'Papelaria', categoria: 'Fornecedores', venc: d(-2), valor: 214.30, origem: 'Print enviado (a classificar)', status: 'pago' }
    ],
    receber: [
      { cliente: 'alfa', servico: 'Consultoria mensal', venc: d(4), valor: 9500.00 },
      { cliente: 'beta', servico: 'Manutenção de sistemas', venc: d(10), valor: 6800.00 },
      { cliente: 'gama', servico: 'Treinamento', venc: d(18), valor: 4200.00 },
      { cliente: 'alfa', servico: 'Projeto de reforma', venc: d(25), valor: 15000.00 }
    ],
    documentos: [
      { tipo: 'NFS-e emitida', cliente: 'alfa', servico: 'Consultoria mensal', data: d(-3), arquivo: 'NFSe_0142_Alfa.pdf', status: 'enviado', regra: 'Emitida pela plataforma' },
      { tipo: 'Relatório de serviço', cliente: 'alfa', servico: 'Consultoria mensal', data: d(-3), arquivo: 'Relatorio_out_Alfa.pdf', status: 'enviado', regra: 'Upload manual' },
      { tipo: 'Orçamento de fornecedor', cliente: 'alfa', servico: 'Projeto de reforma', data: d(-1), arquivo: 'Orcamento_materiais.pdf', status: 'pendente', regra: 'Remetente: fornecedor de materiais' },
      { tipo: 'NFS-e emitida', cliente: 'beta', servico: 'Manutenção de sistemas', data: d(-6), arquivo: 'NFSe_0141_Beta.pdf', status: 'enviado', regra: 'Emitida pela plataforma' },
      { tipo: 'Nota do fornecedor', cliente: 'beta', servico: 'Manutenção de sistemas', data: d(0), arquivo: 'NF_peca_reposicao.pdf', status: 'pendente', regra: 'Remetente: distribuidora de peças' },
      { tipo: 'Contrato', cliente: 'gama', servico: 'Treinamento', data: d(-20), arquivo: 'Contrato_treinamento_Gama.pdf', status: 'enviado', regra: 'Upload manual' },
      { tipo: 'Guia DAS', cliente: null, servico: null, data: d(-1), arquivo: 'DAS_competencia.pdf', status: 'pendente', regra: 'Remetente: escritório · layout DAS' },
      { tipo: 'Boleto de honorários', cliente: null, servico: null, data: d(-1), arquivo: 'Boleto_honorarios.pdf', status: 'pendente', regra: 'Remetente: escritório · linha digitável' },
      { tipo: 'Imagem sem padrão', cliente: null, servico: null, data: d(0), arquivo: 'IMG_2231.jpg', status: 'classificar', regra: 'Nenhuma regra reconheceu' }
    ]
  };
})();
