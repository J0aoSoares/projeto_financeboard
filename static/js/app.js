let tipoSelecionado = 'entrada';

document.getElementById('f-data').value = new Date().toISOString().split('T')[0];

const hoje = new Date();
const mesAtual = `${hoje.getFullYear()}-${String(hoje.getMonth()+1).padStart(2,'0')}`;
document.getElementById('mes-select').value = mesAtual;
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

carregarDados();