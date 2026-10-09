"""db.py — conexão com o MySQL e duas funções de apoio."""
import os

import pymysql


def conectar():
    """Abre uma conexão nova com o banco 'clinica'."""
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "clinica"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,  # cada linha vira um dicionário
    )


def consultar(sql, parametros=(), um=False):
    """Executa um SELECT. Devolve uma lista de dicionários (ou um só, com um=True)."""
    conexao = conectar()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(sql, parametros)  # %s + parâmetros: nunca concatene texto!
            return cursor.fetchone() if um else cursor.fetchall()
    finally:
        conexao.close()


def executar(sql, parametros=()):
    """Executa INSERT, UPDATE ou DELETE e confirma (COMMIT). Devolve o id gerado."""
    conexao = conectar()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(sql, parametros)
        conexao.commit()
        return cursor.lastrowid
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()