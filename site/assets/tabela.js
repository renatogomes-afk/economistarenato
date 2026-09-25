/* Renderiza uma base aberta (dados/<slug>.json) como tabela com busca e ordenacao.
   Uso: <div id="tabela" data-base="municipios-ms"></div> + este script. */
(function () {
  var alvo = document.getElementById('tabela');
  if (!alvo) return;

  var slug = alvo.dataset.base;
  var estado = { dados: [], colunas: [], ordem: null, desc: true, busca: '' };

  var nf = new Intl.NumberFormat('pt-BR');
  var nf2 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });

  function formata(v, tipo) {
    if (v === '' || v === null || v === undefined) return '—';
    if (tipo === 'inteiro') return nf.format(v);
    if (tipo === 'decimal') return nf2.format(v);
    return String(v);
  }

  function numerica(tipo) { return tipo === 'inteiro' || tipo === 'decimal'; }

  function largura(c) { return c.min || (numerica(c.tipo) ? 120 : 160); }

  function filtradas() {
    var b = estado.busca.trim().toLowerCase();
    var linhas = !b ? estado.dados.slice() : estado.dados.filter(function (r) {
      return estado.colunas.some(function (c) {
        return String(r[c.campo]).toLowerCase().indexOf(b) !== -1;
      });
    });
    if (estado.ordem) {
      var col = estado.colunas.find(function (c) { return c.campo === estado.ordem; });
      linhas.sort(function (x, y) {
        var a = x[col.campo], z = y[col.campo];
        if (numerica(col.tipo)) { a = a === '' ? -Infinity : a; z = z === '' ? -Infinity : z; return estado.desc ? z - a : a - z; }
        return estado.desc ? String(z).localeCompare(String(a), 'pt-BR') : String(a).localeCompare(String(z), 'pt-BR');
      });
    }
    return linhas;
  }

  function pinta() {
    var linhas = filtradas();
    var cab = estado.colunas.map(function (c) {
      var seta = estado.ordem === c.campo ? (estado.desc ? ' ▾' : ' ▴') : '';
      return '<th class="' + (numerica(c.tipo) ? 'num' : '') + '" data-campo="' + c.campo +
        '" style="min-width:' + largura(c) + 'px">' +
        c.titulo + '<span class="seta">' + seta + '</span></th>';
    }).join('');

    var corpo = linhas.map(function (r) {
      return '<tr>' + estado.colunas.map(function (c) {
        return '<td class="' + (numerica(c.tipo) ? 'num' : '') + '">' + formata(r[c.campo], c.tipo) + '</td>';
      }).join('') + '</tr>';
    }).join('');

    var minTotal = estado.colunas.reduce(function (t, c) { return t + largura(c); }, 0);
    alvo.querySelector('.tabela-rolagem').innerHTML =
      '<table class="tabela" style="min-width:' + minTotal + 'px"><thead><tr>' + cab +
      '</tr></thead><tbody>' + corpo + '</tbody></table>';

    var rolagem = alvo.querySelector('.tabela-rolagem');
    alvo.querySelector('.tabela-dica').hidden = rolagem.scrollWidth <= rolagem.clientWidth + 4;

    alvo.querySelector('.contagem').textContent =
      linhas.length === estado.dados.length
        ? estado.dados.length + ' linhas'
        : linhas.length + ' de ' + estado.dados.length + ' linhas';

    alvo.querySelectorAll('th').forEach(function (th) {
      th.addEventListener('click', function () {
        var campo = th.dataset.campo;
        if (estado.ordem === campo) { estado.desc = !estado.desc; }
        else { estado.ordem = campo; estado.desc = true; }
        pinta();
      });
    });
  }

  alvo.innerHTML =
    '<div class="tabela-barra">' +
      '<input class="tabela-busca" type="search" placeholder="Buscar nesta base…" aria-label="Buscar">' +
      '<span class="contagem"></span>' +
      '<span class="tabela-baixar">' +
        '<a class="chip" href="../' + slug + '.csv" download>Baixar CSV</a>' +
        '<a class="chip" href="../' + slug + '.json" download>Baixar JSON</a>' +
      '</span>' +
    '</div>' +
    '<div class="tabela-rolagem"><p class="tabela-carregando">Carregando a base…</p></div>' +
    '<p class="tabela-dica" hidden>Arraste a tabela para o lado para ver todas as colunas — ' +
    'ou baixe o arquivo, que vem completo.</p>';

  alvo.querySelector('.tabela-busca').addEventListener('input', function (e) {
    estado.busca = e.target.value; pinta();
  });

  fetch('../' + slug + '.json')
    .then(function (r) { return r.json(); })
    .then(function (j) {
      estado.dados = j.dados;
      estado.colunas = j.meta.colunas;
      pinta();
    })
    .catch(function () {
      alvo.querySelector('.tabela-rolagem').innerHTML =
        '<p class="tabela-carregando">Não foi possível carregar a base agora. ' +
        'O arquivo continua disponível para download acima.</p>';
    });
})();
