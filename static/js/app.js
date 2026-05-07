let tipoSelecionado = 'entrada';

document.getElementById('f-data').value = new Date().toISOString().split('T')[0];

const hoje = new Date();
const mesAtual = `${hoje.getFullYear()}-${String(hoje.getMonth()+1).padStart(2,'0')}`;
document.getElementById('mes-select').value = mesAtual;
document.getElementById('exp-de').value  = mesAtual;
document.getElementById('exp-ate').value = mesAtual;
document.getElementById('mes-select').addEventListener('change', carregarDados);

function setTipo(tipo) {
  tipoSelecionado = tipo;
  document.getElementById('btn-entrada').className = 'tipo-btn' + (tipo === 'entrada' ? ' active-entrada' : '');
  document.getElementById('btn-saida').className   = 'tipo-btn' + (tipo === 'saida'   ? ' active-saida'   : '');
}

function fmt(valor) {
  return valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

async function carregarDados() {
  const mes = document.getElementById('mes-select').value;

  const [resumo, transacoes] = await Promise.all([
    fetch(`/api/resumo?mes=${mes}`).then(r => r.json()),
    fetch(`/api/transacoes?mes=${mes}`).then(r => r.json())
  ]);

  document.getElementById('total-entradas').textContent = fmt(resumo.total_entradas);
  document.getElementById('total-saidas').textContent   = fmt(resumo.total_saidas);
  document.getElementById('saldo').textContent          = fmt(resumo.saldo);

  const lista = document.getElementById('lista');
  if (transacoes.length === 0) {
    lista.innerHTML = '<div class="vazio">NENHUMA TRANSAÇÃO NESTE MÊS</div>';
    return;
  }

  lista.innerHTML = transacoes.map(t => `
    <div class="transacao" id="tx-${t.id}">
      <div class="left">
        <div class="dot ${t.tipo}"></div>
        <div>
          <div class="desc">${t.descricao}</div>
          <div class="meta">${t.data}</div>
        </div>
      </div>
      <div class="right">
        <span class="valor-tx ${t.tipo}">${t.tipo === 'entrada' ? '+' : '−'} ${fmt(t.valor)}</span>
        <button class="btn-del" onclick="excluir(${t.id})" title="Excluir">✕</button>
      </div>
    </div>
  `).join('');
}

async function adicionarTransacao() {
  const desc  = document.getElementById('f-desc').value.trim();
  const valor = parseFloat(document.getElementById('f-valor').value);
  const data  = document.getElementById('f-data').value;

  if (!desc || !valor || !data) {
    alert('Preencha todos os campos!');
    return;
  }

  await fetch('/api/transacoes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ descricao: desc, valor, tipo: tipoSelecionado, data })
  });

  document.getElementById('f-desc').value  = '';
  document.getElementById('f-valor').value = '';
  carregarDados();
}

async function excluir(id) {
  if (!confirm('Excluir esta transação?')) return;
  await fetch(`/api/transacoes/${id}`, { method: 'DELETE' });
  carregarDados();
}

function exportarCSV() {
  const de  = document.getElementById('exp-de').value;
  const ate = document.getElementById('exp-ate').value;
  if (!de || !ate) { alert('Selecione o período de exportação'); return; }
  window.location.href = `/api/exportar?de=${de}&ate=${ate}`;
}

async function importarCSV() {
  const arquivo = document.getElementById('imp-arquivo').files[0];
  if (!arquivo) { alert('Selecione um arquivo CSV'); return; }

  const form = new FormData();
  form.append('arquivo', arquivo);

  const res = await fetch('/api/importar', { method: 'POST', body: form });
  const dados = await res.json();

  const el = document.getElementById('imp-resultado');
  if (dados.erros.length === 0) {
    el.innerHTML = `<div class="imp-ok">✓ ${dados.inseridos} transações importadas</div>`;
  } else {
    el.innerHTML = `<div class="imp-ok">✓ ${dados.inseridos} importadas</div>
                    <div class="imp-err">${dados.erros.join('<br>')}</div>`;
  }

  document.getElementById('imp-arquivo').value = '';
  carregarDados();
}

function baixarTemplate() {
  window.location.href = '/api/template';
}

carregarDados();

function setTela(tela) {
  const telas = ['transacoes', 'medicao', 'orcamento'];
  telas.forEach(t => {
    document.getElementById(`tela-${t}`).style.display = t === tela ? '' : 'none';
  });
  document.querySelectorAll('.menu-item').forEach(el => el.classList.remove('active'));
  const idx = telas.indexOf(tela);
  document.querySelectorAll('.menu-item')[idx].classList.add('active');
}