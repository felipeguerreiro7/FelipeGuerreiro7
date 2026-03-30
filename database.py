import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ativos.db")


def _conn():
    return sqlite3.connect(DB_PATH)


def inicializar():
    con = _conn()
    con.execute("""
        CREATE TABLE IF NOT EXISTS ativos (
            nome      TEXT PRIMARY KEY,
            classe    TEXT NOT NULL,
            subclasse TEXT,
            fonte     TEXT DEFAULT 'Man'
        )
    """)
    con.commit()
    con.close()


def importar_excel(excel_path: str) -> int:
    """Importa o Excel para o banco sem sobrescrever entradas existentes.
    Retorna o número de novos registros inseridos."""
    df = pd.read_excel(excel_path)
    df.columns = ["nome", "classe", "subclasse", "fonte"]
    df = df.dropna(subset=["nome", "classe"])
    df["nome"] = df["nome"].astype(str).str.strip()
    df["classe"] = df["classe"].astype(str).str.strip()
    df["subclasse"] = df["subclasse"].fillna("").astype(str).str.strip()
    df["fonte"] = df["fonte"].fillna("Auto").astype(str).str.strip()

    con = _conn()
    inseridos = 0
    for _, row in df.iterrows():
        cur = con.execute(
            "INSERT OR IGNORE INTO ativos (nome, classe, subclasse, fonte) VALUES (?, ?, ?, ?)",
            (row["nome"], row["classe"], row["subclasse"], row["fonte"]),
        )
        inseridos += cur.rowcount
    con.commit()
    con.close()
    return inseridos


def buscar(nome: str):
    """Busca exata pelo nome. Retorna (classe, subclasse) ou (None, None)."""
    con = _conn()
    row = con.execute(
        "SELECT classe, subclasse FROM ativos WHERE nome = ?", (nome.strip(),)
    ).fetchone()
    con.close()
    return (row[0], row[1]) if row else (None, None)


def buscar_similares(nome: str, limite: int = 6):
    """Busca entradas cujo nome contenha os primeiros caracteres do ativo."""
    termo = nome.strip()[:15]
    con = _conn()
    rows = con.execute(
        "SELECT nome, classe, subclasse FROM ativos WHERE nome LIKE ? LIMIT ?",
        (f"%{termo}%", limite),
    ).fetchall()
    con.close()
    return rows


def salvar(nome: str, classe: str, subclasse: str, fonte: str = "Man"):
    """Insere ou substitui uma classificação no banco."""
    con = _conn()
    con.execute(
        "INSERT OR REPLACE INTO ativos (nome, classe, subclasse, fonte) VALUES (?, ?, ?, ?)",
        (nome.strip(), classe.strip(), subclasse.strip(), fonte),
    )
    con.commit()
    con.close()


def listar_todos() -> pd.DataFrame:
    con = _conn()
    df = pd.read_sql("SELECT nome, classe, subclasse, fonte FROM ativos ORDER BY nome", con)
    con.close()
    return df


def contar() -> int:
    con = _conn()
    n = con.execute("SELECT COUNT(*) FROM ativos").fetchone()[0]
    con.close()
    return n
