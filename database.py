import sqlite3
from datetime import datetime

DB= "financeiro.db"

def conectar():
    conn = sqlite3.connect(DB)
    #row_factory permite acessar rows pelo nome
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_db():
    """
    Cria as tabelas se ainda não existirem.
    O comando 'CREATE TABLE IF NOT EXISTS' é seguro:
    não apaga dados se a tabela já existir.
    """
    conn = conectar()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS transacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descricao TEXT NOT NULL,
        valor REAL NOT NULL,
        tipo TEXT NOT NULL,
        data TEXT NOT NULL
    )
    """)
    # PRIMARY KEY AUTOINCREMENT -> ID único gerado automaticamente
    # NOT NULL                  -> campo obrigatório
    # CHECK(tipo IN (...))      -> validação de valor aceito

    conn.commit()
    conn.close()
    print("Banco de dados inicializado com sucesso.")

def inserir_transacao(descricao, valor, tipo, categoria, data):
    conn = conectar()
    conn.execute(
        "INSERT INTO transacoes (descricao, valor, tipo, categoria, data) VALUES (?, ?, ?, ?, ?)",
        (descricao, valor, tipo, categoria, data)
    )
    conn.commit()
    conn.close()

def buscar_transacoes(mes=None):
    """
    SQL: SELECT busca dados
         WHERE  filtra — usamos LIKE para comparar parte da data
         ORDER BY ordena do mais recente para o mais antigo
    """
    conn = conectar()

    if mes:
        # LIKE 'YYYY-MM%': corresponde a qualquer string que comece com o ano e mês
        cursor = conn.execute("""
            SELECT * FROM transacoes
            WHERE data LIKE ?
            ORDER BY data DESC
        """, (f"{mes}-%",))
    else:
        cursor = conn.execute("""
            SELECT * FROM transacoes
            ORDER BY data DESC
        """)

    #Converte row em dict para o funcionamento do JSON
    rows = [dict(row) for row in cursor]

    conn.close()
    return rows

def deletar_transacao(id):
    """
    Remove uma transação pelo ID.
    """
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
    conn.close()
    return row

 
def totais_por_categoria(mes=None):
    """
    Soma os valores agrupados por categoria.
 
    SQL: GROUP BY agrupa linhas com o mesmo valor
         ORDER BY ordena pelo total (maior primeiro)
    """
    conn = conectar()
    filtro = (f"{mes}-%",) if mes else ("%",)
 
    cursor = conn.execute("""
        SELECT
            categoria,
            tipo,
            SUM(valor) AS total
        FROM transacoes
        WHERE data LIKE ?
        GROUP BY categoria, tipo
        ORDER BY total DESC
    """, filtro)
 
    return [dict(row) for row in cursor.fetchall()]
