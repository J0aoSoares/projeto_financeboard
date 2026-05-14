import sqlite3

DB = "financeiro.db"

def connect():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def migrate_db():
    conn = connect()
    try:
        conn.execute("ALTER TABLE transactions ADD COLUMN category TEXT NOT NULL DEFAULT 'Outros'")
        conn.commit()
        print("Migration: coluna 'category' adicionada.")
    except Exception:
        pass
    conn.close()

def init_db():
    conn = connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT    NOT NULL,
            amount      REAL    NOT NULL,
            kind        TEXT    NOT NULL CHECK(kind IN ('income', 'expense')),
            date        TEXT    NOT NULL,
            invoice_id  INTEGER DEFAULT NULL,
            category    TEXT    NOT NULL DEFAULT 'Outros'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            number         TEXT    NOT NULL,
            supplier       TEXT    NOT NULL,
            description    TEXT    NOT NULL,
            amount         REAL    NOT NULL,
            issue_date     TEXT    NOT NULL,
            due_date       TEXT    NOT NULL,
            status         TEXT    NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','paid','overdue')),
            file_path      TEXT    DEFAULT NULL,
            transaction_id INTEGER DEFAULT NULL
        )
    """)
    conn.commit()
    conn.close()
    migrate_db()
    print("Database initialized.")

# ── TRANSACTIONS ──

def insert_transaction(description, amount, kind, date, invoice_id=None, category='Outros'):
    conn = connect()
    cursor = conn.execute(
        "INSERT INTO transactions (description, amount, kind, date, invoice_id, category) VALUES (?, ?, ?, ?, ?, ?)",
        (description, amount, kind, date, invoice_id, category)
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def get_transactions(month=None):
    conn = connect()
    if month:
        cursor = conn.execute(
            "SELECT * FROM transactions WHERE date LIKE ? ORDER BY date DESC",
            (f"{month}-%",)
        )
    else:
        cursor = conn.execute("SELECT * FROM transactions ORDER BY date DESC")
    rows = [dict(r) for r in cursor]
    conn.close()
    return rows

def update_transaction(id, description, amount, kind, date, category='Outros'):
    conn = connect()
    conn.execute(
        "UPDATE transactions SET description=?, amount=?, kind=?, date=?, category=? WHERE id=?",
        (description, amount, kind, date, category, id)
    )
    conn.commit()
    conn.close()

def remove_transaction(id):
    conn = connect()
    conn.execute("DELETE FROM transactions WHERE id = ?", (id,))
    conn.commit()
    conn.close()

def monthly_summary(month=None):
    conn = connect()
    filter_ = (f"{month}-%",) if month else ("%",)
    cursor = conn.execute("""
        SELECT
            COALESCE(SUM(CASE WHEN kind = 'income'  THEN amount ELSE 0 END), 0) AS total_income,
            COALESCE(SUM(CASE WHEN kind = 'expense' THEN amount ELSE 0 END), 0) AS total_expenses
        FROM transactions
        WHERE date LIKE ?
    """, filter_)
    row = dict(cursor.fetchone())
    row["balance"] = row["total_income"] - row["total_expenses"]
    conn.close()
    return row

def get_transactions_by_period(from_month=None, to_month=None):
    conn = connect()
    if from_month and to_month:
        cursor = conn.execute(
            "SELECT * FROM transactions WHERE date >= ? AND date <= ? ORDER BY date ASC",
            (f"{from_month}-01", f"{to_month}-31")
        )
    elif from_month:
        cursor = conn.execute(
            "SELECT * FROM transactions WHERE date >= ? ORDER BY date ASC",
            (f"{from_month}-01",)
        )
    elif to_month:
        cursor = conn.execute(
            "SELECT * FROM transactions WHERE date <= ? ORDER BY date ASC",
            (f"{to_month}-31",)
        )
    else:
        cursor = conn.execute("SELECT * FROM transactions ORDER BY date ASC")
    rows = [dict(r) for r in cursor]
    conn.close()
    return rows

# ── CATEGORIES ──

def categories_summary(month=None):
    conn = connect()
    filter_ = (f"{month}-%",) if month else ("%",)
    cursor = conn.execute("""
        SELECT category, SUM(amount) AS total
        FROM transactions
        WHERE kind = 'expense' AND date LIKE ?
        GROUP BY category
        ORDER BY total DESC
    """, filter_)
    rows = [dict(r) for r in cursor]
    conn.close()
    return rows

# ── DASHBOARD ──

def last_months_summary(n=6):
    conn = connect()
    cursor = conn.execute("""
        SELECT
            strftime('%Y-%m', date) AS month,
            COALESCE(SUM(CASE WHEN kind = 'income'  THEN amount ELSE 0 END), 0) AS total_income,
            COALESCE(SUM(CASE WHEN kind = 'expense' THEN amount ELSE 0 END), 0) AS total_expenses
        FROM transactions
        GROUP BY month
        ORDER BY month DESC
        LIMIT ?
    """, (n,))
    rows = [dict(r) for r in cursor]
    conn.close()
    return list(reversed(rows))

def pending_invoices():
    conn = connect()
    cursor = conn.execute(
        "SELECT * FROM invoices WHERE status != 'paid' ORDER BY due_date ASC"
    )
    rows = [dict(r) for r in cursor]
    conn.close()
    return rows

# ── INVOICES ──

def insert_invoice(number, supplier, description, amount, issue_date, due_date, file_path=None):
    conn = connect()
    cursor = conn.execute("""
        INSERT INTO invoices (number, supplier, description, amount, issue_date, due_date, file_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (number, supplier, description, amount, issue_date, due_date, file_path))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def get_invoices(month=None):
    conn = connect()
    if month:
        cursor = conn.execute(
            "SELECT * FROM invoices WHERE due_date LIKE ? ORDER BY due_date ASC",
            (f"{month}-%",)
        )
    else:
        cursor = conn.execute("SELECT * FROM invoices ORDER BY due_date ASC")
    rows = [dict(r) for r in cursor]
    conn.close()
    return rows

def get_invoice(id):
    conn = connect()
    cursor = conn.execute("SELECT * FROM invoices WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def mark_invoice_paid(id, payment_date):
    conn = connect()
    invoice = dict(conn.execute("SELECT * FROM invoices WHERE id = ?", (id,)).fetchone())
    conn.close()
    transaction_id = insert_transaction(
        description=f"NF {invoice['number']} — {invoice['supplier']}",
        amount=invoice["amount"],
        kind="expense",
        date=payment_date,
        invoice_id=id,
        category='Fornecedores'
    )
    conn = connect()
    conn.execute(
        "UPDATE invoices SET status = 'paid', transaction_id = ? WHERE id = ?",
        (transaction_id, id)
    )
    conn.commit()
    conn.close()
    return transaction_id

def update_invoice(id, number, supplier, description, amount, issue_date, due_date):
    conn = connect()
    invoice = dict(conn.execute("SELECT * FROM invoices WHERE id = ?", (id,)).fetchone())
    conn.execute("""
        UPDATE invoices
        SET number=?, supplier=?, description=?, amount=?, issue_date=?, due_date=?
        WHERE id=?
    """, (number, supplier, description, amount, issue_date, due_date, id))
    if invoice["transaction_id"]:
        conn.execute(
            "UPDATE transactions SET description=?, amount=? WHERE id=?",
            (f"NF {number} — {supplier}", amount, invoice["transaction_id"])
        )
    conn.commit()
    conn.close()

def remove_invoice(id):
    conn = connect()
    invoice = dict(conn.execute("SELECT * FROM invoices WHERE id = ?", (id,)).fetchone())
    if invoice["transaction_id"]:
        conn.execute("DELETE FROM transactions WHERE id = ?", (invoice["transaction_id"],))
    conn.execute("DELETE FROM invoices WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return invoice.get("file_path")