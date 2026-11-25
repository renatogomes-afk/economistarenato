// Dados de demonstração. Nenhum dado real da FATO67, de clientes ou de órgãos.
(function () {
  const d = n => { const x = new Date(); x.setHours(0,0,0,0); x.setDate(x.getDate() + n); return x.toISOString().slice(0,10); };
  window.DEMO = {
    saldos: [
      { conta: 'C6 Bank PJ', tipo: 'PJ', saldo: 48320.55 },
      { conta: 'C6 Bank PF', tipo: 'PF', saldo: 3120.10 },
      { conta: 'Mercado Pago PF', tipo: 'PF', saldo: 1875.40 },
      { conta: 'Banco do Brasil PF', tipo: 'PF', saldo: 6210.00 }
    ],
    // Certidões e documentos da empresa, reaproveitados em todas as PIs
    certidoes: [
      { nome: 'CND Federal (Receita e PGFN)', validade: d(62) },
      { nome: 'CND Trabalhista (TST)', validade: d(9) },
      { nome: 'CRF do FGTS', validade: d(21) },
      { nome: 'CND Estadual', validade: d(-3) },
      { nome: 'CND Municipal', validade: d(40) },
      // Certificados de registro: validade própria + certidões internas com vencimento próprio
      { nome: 'CERCA Municipal', validade: d(127), internas: [
        { nome: 'CRF do FGTS', validade: d(-212) }, { nome: 'Certidão municipal', validade: d(-217) },
        { nome: 'Certidão estadual', validade: d(-186) }, { nome: 'Falência e concordata', validade: d(-216) },
        { nome: 'Federal e trabalhista', validade: d(298) }, { nome: 'Alvará', validade: d(36) }, { nome: 'Balanço', validade: d(552) } ] },
      { nome: 'CERCA Estadual', validade: d(148), internas: [
        { nome: 'CRF do FGTS', validade: d(-212) }, { nome: 'Certidão estadual', validade: d(-188) },
        { nome: 'Falência e concordata', validade: d(-218) }, { nome: 'Federal e trabalhista', validade: d(297) }, { nome: 'Balanço', validade: d(552) } ] },
      { nome: 'CRC Município B', validade: d(134), internas: [
        { nome: 'CRF do FGTS', validade: d(-212) }, { nome: 'Certidão municipal', validade: d(-217) },
        { nome: 'Federal e trabalhista', validade: d(298) }, { nome: 'Alvará', validade: d(36) } ] },
      { nome: 'Certidão de falência e concordata', validade: d(27) },
      { nome: 'Comprovante de inscrição no Simples', validade: null },
      { nome: 'Tabela comercial assinada', validade: null },
      { nome: 'Declaração de profissionais habilitados', validade: null }
    ],
    // Regra órgão → documentos exigidos (o certificado de registro muda por órgão)
    padrao: ['CND Trabalhista (TST)', 'Tabela comercial assinada', 'Declaração de profissionais habilitados'],
    orgaos: [
      // mapeado: false = ainda não sabemos o que o órgão exige, então vai tudo (como o Roger faz hoje)
      { nome: 'Prefeitura da Capital', registro: 'CERCA Municipal', extras: [], mapeado: false },
      { nome: 'Câmara Municipal da Capital', registro: 'CERCA Municipal', extras: [], mapeado: false },
      { nome: 'Governo do Estado', registro: 'CERCA Estadual', extras: ['Certidão de falência e concordata', 'Comprovante de inscrição no Simples'], mapeado: true },
      { nome: 'Tribunal de Contas do Estado', registro: 'CERCA Estadual', extras: [], mapeado: false },
      { nome: 'Assembleia Legislativa', registro: 'CERCA Estadual', extras: [], mapeado: true },
      { nome: 'Prefeitura do Município B', registro: 'CRC Município B', extras: ['Certidão de falência e concordata'], mapeado: true }
    ],
    // PI = pedido de inserção: a unidade de organização
    pis: [
      { numero: '10234', orgao: 'Assembleia Legislativa', cliente: 'Agência Exemplo Um', para: 'financeiro@agencia-um.exemplo', data: d(-2),
        pasta: { nf: 'NFSe_0151.pdf', prints: ['print_veiculacao_1.jpg', 'print_veiculacao_2.jpg'] }, status: 'pronta' },
      { numero: '10241', orgao: 'Prefeitura do Município B', cliente: 'Agência Exemplo Dois', para: 'contato@agencia-dois.exemplo', data: d(0),
        pasta: { nf: null, prints: ['print_veiculacao_1.jpg'] }, status: 'pendente' },
      { numero: '10198', orgao: 'Prefeitura da Capital', cliente: 'Agência Exemplo Um', para: 'financeiro@agencia-um.exemplo', data: d(-19),
        pasta: { nf: 'NFSe_0147.pdf', prints: ['print_1.jpg', 'print_2.jpg', 'print_3.jpg'] }, status: 'enviada' }
    ],
    pagar: [
      { desc: 'DAS Simples Nacional', fornecedor: 'Escritório de contabilidade', categoria: 'Impostos', venc: d(3), valor: 3870.40, origem: 'Guia por e-mail', status: 'pendente' },
      { desc: 'Honorários contábeis', fornecedor: 'Escritório de contabilidade', categoria: 'Honorários', venc: d(5), valor: 1450.00, origem: 'Boleto por e-mail', status: 'pendente' },
      { desc: 'Licença de software', fornecedor: 'Fornecedor de software', categoria: 'Fornecedores', venc: d(1), valor: 689.90, origem: 'Boleto por e-mail', status: 'pendente' },
      { desc: 'Aluguel', fornecedor: 'Imobiliária', categoria: 'Despesas fixas', venc: d(8), valor: 4200.00, origem: 'Grupo do WhatsApp', status: 'pendente' },
      { desc: 'Internet e telefone', fornecedor: 'Operadora', categoria: 'Despesas fixas', venc: d(12), valor: 329.90, origem: 'Grupo do WhatsApp', status: 'pendente' },
      { desc: 'Pró-labore', fornecedor: 'Roger', categoria: 'Pessoal', venc: d(15), valor: 6000.00, origem: 'Recorrente', status: 'pendente' }
    ],
    receber: [
      { cliente: 'Agência Exemplo Um', ref: 'PI 10234', venc: d(4), valor: 9500.00 },
      { cliente: 'Agência Exemplo Dois', ref: 'PI 10241', venc: d(20), valor: 6800.00 },
      { cliente: 'Agência Exemplo Um', ref: 'PI 10198', venc: d(10), valor: 15000.00 }
    ],
    // O que chegou no Gmail da empresa e as regras reconheceram (demonstração)
    entrada: [
      { arquivo: 'certidao_estadual.pdf', de: 'e-mail do órgão emissor', parece: 'Certidão estadual, nova versão' },
      { arquivo: 'boleto_honorarios.pdf', de: 'escritório de contabilidade', parece: 'Honorários, vence dia 10' }
    ],
    whatsappExemplo: `25/11/2026 08:14 - Roger: pagar contador 1.450,00 dia 30
25/11/2026 08:20 - Roger: luz escritório R$ 312,40 venc 05/12
25/11/2026 09:02 - Roger: lembrar de ligar pra agência
26/11/2026 07:45 - Roger: aluguel 4200 dia 10`
  };
})();
