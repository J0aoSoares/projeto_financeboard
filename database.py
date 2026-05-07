import sqlite3

DB = "financeiro.db"

def conectar():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_db():
    conn = conectar()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transacoes (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT    NOT NULL,
            valor     REAL    NOT NULL,
            tipo      TEXT    NOT NULL CHECK(tipo IN ('entrada', 'saida')),
            data      TEXT    NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print("Banco de dados inicializado com sucesso.")

def inserir_transacao(descricao, valor, tipo, data):
    conn = conectar()
    conn.execute(
        "INSERT INTO transacoes (descricao, valor, tipo, data) VALUES (?, ?, ?, ?)",
        (descricao, valor, tipo, data)
    )
    conn.commit()
    conn.close()

def buscar_transacoes(mes=None):
    conn = conectar()
    if mes:
        cursor = conn.execute("""
            SELECT * FROM transacoes
            WHERE data LIKE ?
            ORDER BY data DESC
        """, (f"{mes}-%",))
    else:
        cursor = conn.execute("SELECT * FROM transacoes ORDER BY data DESC")
    rows = [dict(row) for row in cursor]
    conn.close()
    return rows

def deletar_transacao(id):
    conn = conectar()
    conn.execute("DELETE FROM transacoes WHERE id = ?", (id,))
    conn.commit()
    conn.close()

def resumo_mensal(mes=None):
    conn = conectar()
    filtro = (f"{mes}-%",) if mes else ("%",)
    cursor = conn.execute("""
        SELECT
            COALESCE(SUM(CASE WHEN tipo = 'entrada' THEN valor ELSE 0 END), 0) AS total_entradas,
            COALESCE(SUM(CASE WHEN tipo = 'saida'   THEN valor ELSE 0 END), 0) AS total_saidas
        FROM transacoes
        WHERE data LIKE ?
    """, filtro)
    row = dict(cursor.fetchone())
    row["saldo"] = row["total_entradas"] - row["total_saidas"]
    conn.close()
    return row
def buscar_periodo(de=None, ate=None):
    conn = conectar()
    if de and ate:
        cursor = conn.execute("""
            SELECT * FROM transacoes
            WHERE data >= ? AND data <= ?
            ORDER BY data ASC
        """, (f"{de}-01", f"{ate}-31"))
    elif de:
        cursor = conn.execute("""
            SELECT * FROM transacoes
            WHERE data >= ?
            ORDER BY data ASC
        """, (f"{de}-01",))
    elif ate:
        cursor = conn.execute("""
            SELECT * FROM transacoes
            WHERE data <= ?
            ORDER BY data ASC
        """, (f"{ate}-31",))
    else:
        cursor = conn.execute("SELECT * FROM transacoes ORDER BY data ASC")
    rows = [dict(row) for row in cursor]
    conn.close()
    return rows