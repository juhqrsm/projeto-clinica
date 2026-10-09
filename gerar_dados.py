"""gerar_dados.py — gera os INSERTs de usuario e paciente com os dados já protegidos.

Rode depois de configurar o .env:   python gerar_dados.py
Copie a saída para o schema.sql. Se você trocar CHAVE_FERNET ou CHAVE_HMAC,
rode de novo: os dados criptografados com a chave antiga não abrem com a nova.
"""
from dotenv import load_dotenv

load_dotenv()

from werkzeug.security import generate_password_hash

import seguranca

USUARIOS = [
    ("Carla Mendes", "carla@clinicavida.com", "Recepcao@2026", "recepcao"),
    ("Rafael Lima", "rafael@clinicavida.com", "Admin@2026", "admin"),
    ("Juliana Rocha", "juliana@clinicavida.com", "Clinica@2026", "recepcao"),
]
PACIENTES = [
    ("Ana Beatriz Souza", "529.982.247-25", "1990-04-12", "(11) 98888-1111", "ana.souza@email.com"),
    ("Bruno Henrique Lima", "111.444.777-35", "1985-09-30", "(11) 97777-2222", None),
    ("Carlos Eduardo Silva", "390.533.447-05", "1972-01-18", "(11) 96666-3333", "carlos.silva@email.com"),
    ("Daniela Silva Costa", "706.458.213-90", "2001-11-05", "(11) 95555-4444", "dani.costa@email.com"),
]


def sql(valor):
    return "NULL" if valor is None else "'" + str(valor).replace("'", "''") + "'"


linhas = [f"  ({sql(n)}, {sql(e)},\n   {sql(generate_password_hash(s))}, {sql(p)})" for n, e, s, p in USUARIOS]
print("INSERT INTO usuario (nome, email, senha_hash, perfil) VALUES\n" + ",\n".join(linhas) + ";\n")

linhas = []
for i, (nome, cpf, nasc, tel, email) in enumerate(PACIENTES):
    linhas.append(
        f"  ({sql(nome)},\n   {sql(seguranca.criptografar(cpf))},\n   {sql(seguranca.hash_busca(cpf))},\n"
        f"   {sql(nasc)}, {sql(seguranca.criptografar(tel))},\n   {sql(email)}, '2026-09-0{i + 1} 09:00:00')")
print("INSERT INTO paciente (nome, cpf_cripto, cpf_hash, data_nascimento,\n"
      "                      telefone_cripto, email, consentimento_em) VALUES\n" + ",\n".join(linhas) + ";")