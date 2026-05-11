let selectedType = 'income';
let invoiceToPay = null;
let transactionToEdit = null;
let editType = 'income';
let loadedTransactions = [];
let invoiceToEdit = null;
let loadedInvoices = [];

// ── INIT ──
document.getElementById('f-date').value = new Date().toISOString().split('T')[0];
document.getElementById('inv-issue-date').value = new Date().toISOString().split('T')[0];

const today = new Date();
const currentMonth = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}`;
document.getElementById('month-select').value  = currentMonth;
document.getElementById('export-from').value   = currentMonth;
document.getElementById('export-to').value     = currentMonth;

document.getElementById('month-select').addEventListener('change', () => {
  const active = document.querySelector('[id^="screen-"]:not([style*="none"])').id.replace('screen-','');
  if (active === 'transactions') loadTransactions();
  if (active === 'invoices')     loadInvoices();
});

// ── NAVIGATION ──
function setScreen(screen) {
  const screens = ['transactions', 'invoices', 'measurement', 'budget'];
  screens.forEach(s => {
    document.getElementById(`screen-${s}`).style.display = s === screen ? '' : 'none';
  });
  document.querySelectorAll('.menu-item').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.menu-item')[screens.indexOf(screen)].classList.add('active');
  if (screen === 'transactions') loadTransactions();
  if (screen === 'invoices')     loadInvoices();
}

// ── UTILS ──
function fmt(value) {
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function invoiceStatus(dueDate, status) {
  if (status === 'paid') return { cls: 'status-paid',    label: 'PAGO' };
  const now  = new Date(); now.setHours(0,0,0,0);
  const due  = new Date(dueDate + 'T00:00:00');
  const diff = Math.ceil((due - now) / 86400000);
  if (diff < 0)  return { cls: 'status-overdue', label: 'VENCIDO' };
  if (diff <= 7) return { cls: 'status-warning', label: `VENCE EM ${diff}D` };
  return { cls: 'status-pending', label: 'PENDENTE' };
}

// ── TRANSACTIONS ──
function setType(type) {
  selectedType = type;
  document.getElementById('btn-income').className  = 'tipo-btn' + (type === 'income'  ? ' active-entrada' : '');
  document.getElementById('btn-expense').className = 'tipo-btn' + (type === 'expense' ? ' active-saida'   : '');
}

async function loadTransactions() {
  const month = document.getElementById('month-select').value;
  const [summary, transactions] = await Promise.all([
    fetch(`/api/summary?month=${month}`).then(r => r.json()),
    fetch(`/api/transactions?month=${month}`).then(r => r.json())
  ]);

  document.getElementById('total-income').textContent   = fmt(summary.total_income);
  document.getElementById('total-expenses').textContent = fmt(summary.total_expenses);
  document.getElementById('balance').textContent        = fmt(summary.balance);

  loadedTransactions = transactions;

  const list = document.getElementById('transaction-list');
  if (transactions.length === 0) {
    list.innerHTML = '<div class="vazio">NENHUMA TRANSAÇÃO NESTE MÊS</div>';
    return;
  }

  list.innerHTML = transactions.map(t => `
    <div class="transacao" id="tx-${t.id}">
      <div class="left">
        <div class="dot ${t.kind === 'income' ? 'entrada' : 'saida'}"></div>
        <div>
          <div class="desc">${t.description}</div>
          <div class="meta">${t.date}${t.invoice_id ? ' · <span class="tag-nf">NF</span>' : ''}</div>
        </div>
      </div>
      <div class="right">
        <span class="valor-tx ${t.kind === 'income' ? 'entrada' : 'saida'}">
          ${t.kind === 'income' ? '+' : '−'} ${fmt(t.amount)}
        </span>
        ${!t.invoice_id ? `
          <button class="btn-icon" onclick="openEditModal(${t.id})" title="Editar">✎</button>
          <button class="btn-del"  onclick="deleteTransaction(${t.id})">✕</button>
        ` : ''}
      </div>
    </div>
  `).join('');
}

async function addTransaction() {
  const description = document.getElementById('f-desc').value.trim();
  const amount      = parseFloat(document.getElementById('f-amount').value);
  const date        = document.getElementById('f-date').value;
  if (!description || !amount || !date) { alert('Preencha todos os campos!'); return; }
  await fetch('/api/transactions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ description, amount, kind: selectedType, date })
  });
  document.getElementById('f-desc').value   = '';
  document.getElementById('f-amount').value = '';
  loadTransactions();
}

async function deleteTransaction(id) {
  if (!confirm('Excluir esta transação?')) return;
  await fetch(`/api/transactions/${id}`, { method: 'DELETE' });
  loadTransactions();
}

// ── EDIT MODAL ──
function setEditType(type) {
  editType = type;
  document.getElementById('edit-btn-income').className  = 'tipo-btn' + (type === 'income'  ? ' active-entrada' : '');
  document.getElementById('edit-btn-expense').className = 'tipo-btn' + (type === 'expense' ? ' active-saida'   : '');
}

function openEditModal(id) {
  const t = loadedTransactions.find(tx => tx.id === id);
  if (!t) return;
  transactionToEdit = id;
  document.getElementById('edit-desc').value   = t.description;
  document.getElementById('edit-amount').value  = t.amount;
  document.getElementById('edit-date').value    = t.date;
  setEditType(t.kind);
  document.getElementById('edit-modal').style.display = 'flex';
}

function closeEditModal() {
  document.getElementById('edit-modal').style.display = 'none';
  transactionToEdit = null;
}

async function confirmEdit() {
  const description = document.getElementById('edit-desc').value.trim();
  const amount      = parseFloat(document.getElementById('edit-amount').value);
  const date        = document.getElementById('edit-date').value;
  if (!description || !amount || !date) { alert('Preencha todos os campos!'); return; }
  await fetch(`/api/transactions/${transactionToEdit}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ description, amount, kind: editType, date })
  });
  closeEditModal();
  loadTransactions();
}

// ── CSV ──
function exportCSV() {
  const from = document.getElementById('export-from').value;
  const to   = document.getElementById('export-to').value;
  if (!from || !to) { alert('Selecione o período de exportação'); return; }
  window.location.href = `/api/export?from=${from}&to=${to}`;
}

async function importCSV() {
  const file = document.getElementById('import-file').files[0];
  if (!file) { alert('Selecione um arquivo CSV'); return; }
  const form = new FormData();
  form.append('file', file);
  const res  = await fetch('/api/import', { method: 'POST', body: form });
  const data = await res.json();
  const el   = document.getElementById('import-result');
  el.innerHTML = data.errors.length === 0
    ? `<div class="imp-ok">✓ ${data.inserted} transações importadas</div>`
    : `<div class="imp-ok">✓ ${data.inserted} importadas</div><div class="imp-err">${data.errors.join('<br>')}</div>`;
  document.getElementById('import-file').value = '';
  loadTransactions();
}

function downloadTemplate() { window.location.href = '/api/template'; }

// ── EDIT INVOICE MODAL ──
function openEditInvoiceModal(id) {
  const inv = loadedInvoices.find(i => i.id === id);
  if (!inv) return;
  invoiceToEdit = id;
  document.getElementById('einv-number').value      = inv.number;
  document.getElementById('einv-supplier').value    = inv.supplier;
  document.getElementById('einv-description').value = inv.description;
  document.getElementById('einv-amount').value      = inv.amount;
  document.getElementById('einv-issue-date').value  = inv.issue_date;
  document.getElementById('einv-due-date').value    = inv.due_date;
  document.getElementById('einv-paid-notice').style.display = inv.status === 'paid' ? 'block' : 'none';
  document.getElementById('edit-invoice-modal').style.display = 'flex';
}

function closeEditInvoiceModal() {
  document.getElementById('edit-invoice-modal').style.display = 'none';
  invoiceToEdit = null;
}

async function confirmEditInvoice() {
  const number      = document.getElementById('einv-number').value.trim();
  const supplier    = document.getElementById('einv-supplier').value.trim();
  const description = document.getElementById('einv-description').value.trim();
  const amount      = parseFloat(document.getElementById('einv-amount').value);
  const issueDate   = document.getElementById('einv-issue-date').value;
  const dueDate     = document.getElementById('einv-due-date').value;
  if (!number || !supplier || !description || !amount || !issueDate || !dueDate) {
    alert('Preencha todos os campos!'); return;
  }
  await fetch(`/api/invoices/${invoiceToEdit}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ number, supplier, description, amount, issue_date: issueDate, due_date: dueDate })
  });
  closeEditInvoiceModal();
  loadInvoices();
  loadTransactions();
}

// ── INVOICES ──
async function loadInvoices() {
  const month   = document.getElementById('month-select').value;
  const invoices = await fetch(`/api/invoices?month=${month}`).then(r => r.json());

  const total   = invoices.reduce((s, i) => s + i.amount, 0);
  const pending = invoices.filter(i => i.status !== 'paid').length;
  const paid    = invoices.filter(i => i.status === 'paid').length;
  document.getElementById('inv-total').textContent   = fmt(total);
  document.getElementById('inv-pending').textContent = pending;
  document.getElementById('inv-paid').textContent    = paid;

  loadedInvoices = invoices;

  const list = document.getElementById('invoice-list');
  if (invoices.length === 0) {
    list.innerHTML = '<div class="vazio">NENHUMA NOTA NESTE MÊS</div>';
    return;
  }

  list.innerHTML = invoices.map(inv => {
    const s = invoiceStatus(inv.due_date, inv.status);
    return `
      <div class="transacao">
        <div class="left" style="flex:1;gap:16px">
          <div class="nota-status ${s.cls}">${s.label}</div>
          <div style="flex:1">
            <div class="desc">${inv.supplier} <span class="tag-nf">${inv.number}</span></div>
            <div class="meta">${inv.description} · vence ${inv.due_date}</div>
          </div>
        </div>
        <div class="right" style="gap:8px">
          <span class="valor-tx saida">− ${fmt(inv.amount)}</span>
          ${inv.file_path ? `<button class="btn-icon" onclick="window.open('/api/invoices/${inv.id}/file')" title="Ver PDF">📄</button>` : ''}
          ${inv.status !== 'paid' ? `<button class="btn-icon btn-pagar" onclick="openPayModal(${inv.id}, '${inv.supplier}', ${inv.amount})">✓</button>` : ''}
          <button class="btn-icon" onclick="openEditInvoiceModal(${inv.id})" title="Editar">✎</button>
          <button class="btn-del" onclick="deleteInvoice(${inv.id})">✕</button>
        </div>
      </div>
    `;
  }).join('');
}

async function addInvoice() {
  const number      = document.getElementById('inv-number').value.trim();
  const supplier    = document.getElementById('inv-supplier').value.trim();
  const description = document.getElementById('inv-description').value.trim();
  const amount      = document.getElementById('inv-amount').value;
  const issueDate   = document.getElementById('inv-issue-date').value;
  const dueDate     = document.getElementById('inv-due-date').value;
  const file        = document.getElementById('inv-file').files[0];

  if (!number || !supplier || !description || !amount || !issueDate || !dueDate) {
    alert('Preencha todos os campos obrigatórios!'); return;
  }

  const form = new FormData();
  form.append('number',      number);
  form.append('supplier',    supplier);
  form.append('description', description);
  form.append('amount',      amount);
  form.append('issue_date',  issueDate);
  form.append('due_date',    dueDate);
  if (file) form.append('file', file);

  await fetch('/api/invoices', { method: 'POST', body: form });
  ['inv-number','inv-supplier','inv-description','inv-amount','inv-due-date'].forEach(id => {
    document.getElementById(id).value = '';
  });
  document.getElementById('inv-file').value = '';
  loadInvoices();
}

async function deleteInvoice(id) {
  if (!confirm('Excluir esta nota? Se já estiver paga, a transação vinculada também será removida.')) return;
  await fetch(`/api/invoices/${id}`, { method: 'DELETE' });
  loadInvoices();
  loadTransactions();
}

// ── PAY MODAL ──
function openPayModal(id, supplier, amount) {
  invoiceToPay = id;
  document.getElementById('modal-desc').textContent = `${supplier} — ${fmt(amount)}`;
  document.getElementById('modal-date').value = new Date().toISOString().split('T')[0];
  document.getElementById('pay-modal').style.display = 'flex';
}

function closeModal() {
  document.getElementById('pay-modal').style.display = 'none';
  invoiceToPay = null;
}

async function confirmPayment() {
  const date = document.getElementById('modal-date').value;
  if (!date) { alert('Informe a data do pagamento'); return; }
  await fetch(`/api/invoices/${invoiceToPay}/pay`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ payment_date: date })
  });
  closeModal();
  loadInvoices();
  loadTransactions();
}

loadTransactions();