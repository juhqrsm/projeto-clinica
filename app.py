"""app.py — Sistema da Clínica Médica (Flask)."""
import os
import time
from datetime import date, datetime, timedelta
from functools import wraps

from dotenv import load_dotenv

load_dotenv()  # lê o .env ANTES de importar seguranca.py, que usa as chaves

from flask import Flask, flash, redirect, render_template, request, session, url_for
from pymysql.err import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash


import seguranca
from db import consultar, executar

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        if not email or not senha:
            flash("Preencha o e-mail e a senha.", "erro")
            return render_template("login.html", email=email), 400

        usuario = consultar("SELECT * FROM usuario WHERE email = %s", (email,), um=True)
        if usuario is None or not check_password_hash(usuario["senha_hash"], senha):
            # mesma mensagem para e-mail e senha: não revela qual dos dois errou
            flash("E-mail ou senha inválidos.", "erro")
            return render_template("login.html", email=email), 401

        session.clear()
        session.permanent = True
        session["usuario_id"] = usuario["id_usuario"]
        session["usuario_nome"] = usuario["nome"]
        session["ultimo_acesso"] = time.time()
        return redirect(url_for("painel"))
    return render_template("login.html")

# ---------- sessão com tempo de expiração ----------
MINUTOS = int(os.getenv("SESSAO_MINUTOS", "15"))
app.permanent_session_lifetime = timedelta(minutes=MINUTOS)
app.config["SESSION_COOKIE_HTTPONLY"] = True   # o JavaScript da página não lê o cookie
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


def login_obrigatorio(funcao):
    """Decorator: só deixa entrar quem fez login e não ficou parado demais."""
    @wraps(funcao)
    def verificar(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Faça login para continuar.", "aviso")
            return redirect(url_for("login"))
        if time.time() - session.get("ultimo_acesso", 0) > MINUTOS * 60:
            session.clear()
            flash(f"Sua sessão expirou após {MINUTOS} minutos sem uso. Entre de novo.", "aviso")
            return redirect(url_for("login"))
        session["ultimo_acesso"] = time.time()  # cada clique renova o prazo
        return funcao(*args, **kwargs)
    return verificar

# ---------- filtros personalizados do Jinja2 ----------
@app.template_filter("data_br")
def data_br_filter(valor):
    """Converte date/datetime ou string YYYY-MM-DD para DD/MM/YYYY."""
    if not valor:
        return ""
    if isinstance(valor, (date, datetime)):
        return valor.strftime("%d/%m/%Y")
    try:
        dt = datetime.strptime(str(valor), "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except ValueError:
        return str(valor)

@app.template_filter("hora")
def hora_filter(valor):
    """Converte time, timedelta ou string HH:MM:SS para HH:MM."""
    if not valor:
        return ""
    if isinstance(valor, timedelta):
        tot_sec = int(valor.total_seconds())
        h = tot_sec // 3600
        m = (tot_sec % 3600) // 60
        return f"{h:02d}:{m:02d}"
    if isinstance(valor, (datetime, time.struct_time)):
        return valor.strftime("%H:%M")
    try:
        str_val = str(valor)
        parts = str_val.split(":")
        return f"{int(parts[0]):02d}:{int(parts[1]):02d}"
    except (ValueError, IndexError):
        return str(valor)

@app.context_processor
def usuario_logado():
    """Deixa o nome do usuário disponível em todos os templates."""
    return {"usuario_nome": session.get("usuario_nome")}

@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu do sistema.", "sucesso")
    return redirect(url_for("login"))

# ---------- página principal ----------
@app.route("/")
@login_obrigatorio
def painel():
    hoje = date.today()
    totais = {
        "pacientes": consultar("SELECT COUNT(*) AS n FROM paciente", um=True)["n"],
        "medicos": consultar("SELECT COUNT(*) AS n FROM medico", um=True)["n"],
        "proximas": consultar(
            "SELECT COUNT(*) AS n FROM agendamento WHERE data_consulta >= %s AND status = 'agendada'",
            (hoje,), um=True)["n"],
    }
    proximos = consultar(
        """SELECT a.data_consulta, a.hora_consulta, p.nome AS paciente, m.nome AS medico
           FROM agendamento a
           JOIN paciente p ON p.id_paciente = a.id_paciente
           JOIN medico   m ON m.id_medico   = a.id_medico
           WHERE a.data_consulta >= %s AND a.status = 'agendada'
           ORDER BY a.data_consulta, a.hora_consulta
           LIMIT 3""", (hoje,))
    return render_template("painel.html", totais=totais, proximos=proximos)

# ---------- pacientes ----------
@app.route("/pacientes")
@login_obrigatorio
def pacientes():
    termo = request.args.get("q", "").strip()
    sql = "SELECT id_paciente, nome, cpf_cripto, data_nascimento, telefone_cripto FROM paciente"
    if len(seguranca.so_digitos(termo)) == 11:          # parece um CPF: busca pelo hash
        linhas = consultar(sql + " WHERE cpf_hash = %s", (seguranca.hash_busca(termo),))
    elif termo:                                         # senão, busca pelo nome
        linhas = consultar(sql + " WHERE nome LIKE %s ORDER BY nome", (f"%{termo}%",))
    else:
        linhas = consultar(sql + " ORDER BY nome")

    for p in linhas:  # descriptografa só para mostrar, e já mascarado
        p["cpf"] = seguranca.mascarar_cpf(seguranca.descriptografar(p["cpf_cripto"]))
        p["telefone"] = seguranca.descriptografar(p["telefone_cripto"])
    return render_template("pacientes.html", pacientes=linhas, termo=termo)

@app.route("/pacientes/novo", methods=["GET", "POST"])
@login_obrigatorio
def novo_paciente():
    if request.method == "POST":
        f = request.form
        nome = f.get("nome", "").strip()
        cpf = f.get("cpf", "").strip()
        nascimento = f.get("data_nascimento", "")
        telefone = f.get("telefone", "").strip()
        email = f.get("email", "").strip().lower() or None

        erros = []
        if not nome or not cpf or not nascimento or not telefone:
            erros.append("Preencha nome, CPF, data de nascimento e telefone.")
        if cpf and not seguranca.cpf_valido(cpf):
            erros.append("CPF inválido: confira os dígitos.")
        if not f.get("consentimento"):
            erros.append("O paciente precisa consentir com o uso dos dados (LGPD).")
        if not erros and consultar("SELECT 1 FROM paciente WHERE cpf_hash = %s",
                                   (seguranca.hash_busca(cpf),), um=True):
            erros.append("Já existe um paciente com este CPF.")
        if erros:
            for e in erros:
                flash(e, "erro")
            return render_template("paciente_form.html", dados=f), 400

        executar(
            """INSERT INTO paciente (nome, cpf_cripto, cpf_hash, data_nascimento,
                                     telefone_cripto, email, consentimento_em)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (nome, seguranca.criptografar(seguranca.formatar_cpf(cpf)), seguranca.hash_busca(cpf),
             nascimento, seguranca.criptografar(telefone), email, datetime.now()))
        flash(f"Paciente {nome} cadastrado.", "sucesso")
        return redirect(url_for("pacientes"))
    return render_template("paciente_form.html", dados={})

# ---------- médicos ----------
@app.route("/medicos")
@login_obrigatorio
def medicos():
    linhas = consultar("SELECT * FROM medico ORDER BY nome")
    return render_template("medicos.html", medicos=linhas)


@app.route("/medicos/novo", methods=["GET", "POST"])
@login_obrigatorio
def novo_medico():
    if request.method == "POST":
        f = request.form
        nome, crm, especialidade = f.get("nome", "").strip(), f.get("crm", "").strip().upper(), f.get("especialidade", "").strip()
        if not nome or not crm or not especialidade:
            flash("Preencha nome, CRM e especialidade.", "erro")
            return render_template("medico_form.html", dados=f), 400
        try:
            executar("INSERT INTO medico (nome, crm, especialidade, email) VALUES (%s, %s, %s, %s)",
                     (nome, crm, especialidade, f.get("email", "").strip().lower() or None))
        except IntegrityError:  # UNIQUE no crm
            flash("Já existe um médico com este CRM.", "erro")
            return render_template("medico_form.html", dados=f), 400
        flash(f"{nome} cadastrado(a).", "sucesso")
        return redirect(url_for("medicos"))
    return render_template("medico_form.html", dados={})

# ---------- agendamentos ----------
@app.route("/agendamentos")
@login_obrigatorio
def agendamentos():
    linhas = consultar(
        """SELECT a.id_agendamento, a.data_consulta, a.hora_consulta, a.status,
                  p.nome AS paciente, p.telefone_cripto,
                  m.nome AS medico, m.especialidade
           FROM agendamento a
           JOIN paciente p ON p.id_paciente = a.id_paciente
           JOIN medico   m ON m.id_medico   = a.id_medico
           ORDER BY a.data_consulta, a.hora_consulta""")
    for a in linhas:
        a["telefone"] = seguranca.descriptografar(a["telefone_cripto"])
    return render_template("agendamentos.html", agendamentos=linhas)


@app.route("/agendamentos/novo", methods=["GET", "POST"])
@login_obrigatorio
def novo_agendamento():
    lista_pacientes = consultar("SELECT id_paciente, nome FROM paciente ORDER BY nome")
    lista_medicos = consultar("SELECT id_medico, nome, especialidade FROM medico ORDER BY nome")

    if request.method == "POST":
        f = request.form
        paciente, medico = f.get("id_paciente"), f.get("id_medico")
        data_txt, hora = f.get("data_consulta", ""), f.get("hora_consulta", "")

        # --- AQUI: Ajusta "14:00" para "14:00:00" antes das validações ---
        if hora and len(hora) == 5:
            hora = f"{hora}:00"

        erros = []
        if not paciente or not medico or not data_txt or not hora:
            erros.append("Escolha o paciente, o médico, a data e o horário.")
        elif datetime.strptime(data_txt, "%Y-%m-%d").date() < date.today():
            erros.append("A data da consulta não pode estar no passado.")
        if not erros:
            try:
                executar(
                    """INSERT INTO agendamento (id_paciente, id_medico, data_consulta,
                                                hora_consulta, observacao, criado_por)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (paciente, medico, data_txt, hora, f.get("observacao", "").strip() or None,
                     session["usuario_id"]))
            except IntegrityError:  # UNIQUE (id_medico, data_consulta, hora_consulta)
                erros.append("Este médico já tem consulta neste dia e horário.")
        if erros:
            for e in erros:
                flash(e, "erro")
            return render_template("agendamento_form.html", dados=f,
                                   pacientes=lista_pacientes, medicos=lista_medicos), 400
        flash("Consulta agendada.", "sucesso")
        return redirect(url_for("agendamentos"))

    return render_template("agendamento_form.html", dados={},
                           pacientes=lista_pacientes, medicos=lista_medicos)

# ---------- usuarios ----------

@app.route("/usuarios", methods=["GET", "POST"])
@login_obrigatorio
def usuarios():
    if request.method == "POST":
        f = request.form
        nome = f.get("nome", "").strip()
        email = f.get("email", "").strip()
        senha = f.get("senha", "").strip()

        erros = []
        if not nome or not email or not senha:
            erros.append("Preencha todos os campos obrigatórios (Nome, E-mail e Senha).")

        if not erros:
            try:
                # Criptografa a senha antes de salvar no banco
                hash_senha = generate_password_hash(senha)
                
                # CORRIGIDO: usando o nome exato da coluna 'senha_hash'
                executar(
                    "INSERT INTO usuario (nome, email, senha_hash) VALUES (%s, %s, %s)",
                    (nome, email, hash_senha)
                )
                flash("Usuário cadastrado com sucesso!", "sucesso")
                return redirect(url_for("usuarios"))
            except IntegrityError:
                erros.append("Este e-mail já está cadastrado no sistema.")
            except Exception as e:
                erros.append(f"Erro ao salvar usuário: {e}")

        if erros:
            for e in erros:
                flash(e, "erro")

    lista_usuarios = consultar("SELECT id_usuario, nome, email, perfil FROM usuario ORDER BY nome")
    return render_template("usuarios.html", usuarios=lista_usuarios, usuario_edit=None)


@app.route("/usuarios/editar/<int:id_usuario>", methods=["GET", "POST"])
@login_obrigatorio
def editar_usuario(id_usuario):
    user = consultar("SELECT id_usuario, nome, email FROM usuario WHERE id_usuario = %s", (id_usuario,))
    if not user:
        flash("Usuário não encontrado.", "erro")
        return redirect(url_for("usuarios"))

    if request.method == "POST":
        f = request.form
        nome = f.get("nome", "").strip()
        email = f.get("email", "").strip()
        senha = f.get("senha", "").strip()

        erros = []
        if not nome or not email:
            erros.append("Nome e E-mail são obrigatórios.")

        if not erros:
            try:
                if senha:
                    # Se informou uma nova senha, atualiza a coluna 'senha_hash'
                    hash_senha = generate_password_hash(senha)
                    executar(
                        "UPDATE usuario SET nome = %s, email = %s, senha_hash = %s WHERE id_usuario = %s",
                        (nome, email, hash_senha, id_usuario)
                    )
                else:
                    # Se não digitou senha nova, atualiza apenas nome e email
                    executar(
                        "UPDATE usuario SET nome = %s, email = %s WHERE id_usuario = %s",
                        (nome, email, id_usuario)
                    )
                flash("Usuário atualizado com sucesso!", "sucesso")
                return redirect(url_for("usuarios"))
            except IntegrityError:
                erros.append("Este e-mail já pertence a outro usuário.")
            except Exception as e:
                erros.append(f"Erro ao atualizar usuário: {e}")

        if erros:
            for e in erros:
                flash(e, "erro")

    lista_usuarios = consultar("SELECT id_usuario, nome, email, perfil FROM usuario ORDER BY nome")
    return render_template("usuarios.html", usuarios=lista_usuarios, usuario_edit=user[0])


@app.route("/usuarios/excluir/<int:id_usuario>", methods=["POST"])
@login_obrigatorio
def excluir_usuario(id_usuario):
    # Regra de segurança: impede excluir a própria conta em uso
    if id_usuario == session.get("usuario_id"):
        flash("Você não pode excluir o seu próprio usuário enquanto está logado!", "erro")
        return redirect(url_for("usuarios"))

    try:
        executar("DELETE FROM usuario WHERE id_usuario = %s", (id_usuario,))
        flash("Usuário excluído com sucesso!", "sucesso")
    except IntegrityError:
        flash("Não é possível excluir este usuário pois ele possui registros (agendamentos) vinculados.", "erro")
    except Exception as e:
        flash(f"Erro ao excluir usuário: {e}", "erro")

    return redirect(url_for("usuarios"))

if __name__ == "__main__":
    app.run(debug=True)