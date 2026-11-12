from flask import (
    Flask, render_template, request, redirect, url_for,
    session, g, flash
)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
import os
import secrets
import getpass

# ==========================================
# CONFIGURAÇÕES
# ==========================================

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)

SECRET_FILE = INSTANCE_DIR / "secret_key.txt"
SECRET_KEY = os.environ.get("SECRET_KEY")

if not SECRET_KEY:
    if SECRET_FILE.exists():
        SECRET_KEY = SECRET_FILE.read_text(encoding="utf-8").strip()
    else:
        SECRET_KEY = secrets.token_hex(32)
        SECRET_FILE.write_text(SECRET_KEY, encoding="utf-8")

app = Flask(__name__)

app.config.update(
    SECRET_KEY=SECRET_KEY,
    SQLALCHEMY_DATABASE_URI=f"sqlite:///{BASE_DIR / 'remaneio.db'}",
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "0") == "1",
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    WTF_CSRF_TIME_LIMIT=3600,
    MAX_CONTENT_LENGTH=1024 * 1024,
)

db = SQLAlchemy(app)
csrf = CSRFProtect(app)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# ==========================================
# MODELOS DO BANCO DE DADOS
# ==========================================

class Pesagem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    placa = db.Column(db.String(20), nullable=False)
    peso_bruto = db.Column(db.Float, nullable=False)
    tara = db.Column(db.Float, nullable=False)
    peso_inicial = db.Column(db.Float, nullable=False)
    data_hora = db.Column(db.String(20), nullable=False)


class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_usuario = db.Column(db.String(80), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(20), nullable=False, default="operador")
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


with app.app_context():
    db.create_all()


# ==========================================
# CONTROLE DE LOGIN E PERMISSÕES
# ==========================================

@app.before_request
def carregar_usuario_logado():
    g.usuario = None
    usuario_id = session.get("usuario_id")

    if usuario_id:
        usuario = db.session.get(Usuario, usuario_id)

        if usuario and usuario.ativo:
            g.usuario = usuario
        else:
            session.clear()


@app.context_processor
def disponibilizar_usuario():
    return {"usuario_atual": getattr(g, "usuario", None)}


def login_obrigatorio(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not g.usuario:
            flash("Faça login para acessar essa página.", "aviso")
            return redirect(url_for("login"))

        return func(*args, **kwargs)

    return wrapper


def administrador_obrigatorio(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not g.usuario:
            flash("Faça login para acessar essa página.", "aviso")
            return redirect(url_for("login"))

        if g.usuario.tipo != "administrador":
            return render_template(
                "erro_permissao.html",
                mensagem="Seu tipo de usuário não permite realizar essa ação."
            ), 403

        return func(*args, **kwargs)

    return wrapper


# ==========================================
# PROTEÇÕES ADICIONAIS
# ==========================================

@app.after_request
def adicionar_cabecalhos_seguranca(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=()"
    )
    response.headers["Cache-Control"] = "no-store"

    return response


# ==========================================
# LOGIN
# ==========================================

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login():

    if g.usuario:
        return redirect(url_for("index"))

    mensagem = ""

    if request.method == "POST":

        nome_usuario = request.form.get(
            "nome_usuario", ""
        ).strip().lower()

        senha = request.form.get("senha", "")

        usuario = Usuario.query.filter_by(
            nome_usuario=nome_usuario
        ).first()

        if (
            usuario
            and usuario.ativo
            and check_password_hash(usuario.senha_hash, senha)
        ):
            session.clear()
            session["usuario_id"] = usuario.id
            session.permanent = True

            return redirect(url_for("index"))

        mensagem = "Usuário ou senha incorretos."

    return render_template("login.html", mensagem=mensagem)


# ==========================================
# SAIR DO SISTEMA
# ==========================================

@app.route("/sair", methods=["POST"])
@login_obrigatorio
def sair():

    session.clear()

    flash("Você saiu do sistema.", "sucesso")

    return redirect(url_for("login"))


# ==========================================
# PÁGINA INICIAL
# ==========================================

@app.route("/")
def index():

    return render_template("index.html")


# ==========================================
# CADASTRO E LISTAGEM DE PESAGENS
# ==========================================

@app.route("/cadastro-pesagem", methods=["GET", "POST"])
@login_obrigatorio
def cadastro_pesagem():

    mensagem = ""

    if request.method == "POST":

        placa = request.form.get(
            "placa", ""
        ).strip().upper()

        peso_bruto_texto = request.form.get("peso_bruto", "")
        tara_texto = request.form.get("tara", "")

        try:

            peso_bruto = float(peso_bruto_texto)
            tara = float(tara_texto)

            if not placa or len(placa) > 7:
                mensagem = "Informe uma placa válida, com até 7 caracteres."

            elif peso_bruto <= 0 or tara < 0:
                mensagem = "Os pesos informados precisam ser valores válidos."

            elif tara >= peso_bruto:
                mensagem = "A tara não pode ser maior ou igual ao peso bruto."

            else:

                nova_pesagem = Pesagem(
                    placa=placa,
                    peso_bruto=peso_bruto,
                    tara=tara,
                    peso_inicial=peso_bruto - tara,
                    data_hora=datetime.now().strftime("%d/%m/%Y %H:%M")
                )

                db.session.add(nova_pesagem)
                db.session.commit()

                mensagem = "Pesagem registrada com sucesso!"

        except (ValueError, TypeError):

            mensagem = "Digite valores numéricos válidos."

    pesagens = Pesagem.query.order_by(
        Pesagem.id.desc()
    ).all()

    return render_template(
        "cadastro_pesagem.html",
        pesagens=pesagens,
        mensagem=mensagem
    )


# ==========================================
# EXCLUIR PESAGEM - SOMENTE ADMINISTRADOR
# ==========================================

@app.route("/excluir/<int:id>", methods=["POST"])
@administrador_obrigatorio
def excluir(id):

    pesagem = db.session.get(Pesagem, id)

    if pesagem:
        db.session.delete(pesagem)
        db.session.commit()

        flash("Pesagem excluída.", "sucesso")

    return redirect(url_for("cadastro_pesagem"))


# ==========================================
# EDITAR PESAGEM - SOMENTE ADMINISTRADOR
# ==========================================

@app.route("/editar/<int:id>", methods=["GET", "POST"])
@administrador_obrigatorio
def editar(id):

    pesagem = db.session.get(Pesagem, id)

    if pesagem is None:
        return redirect(url_for("cadastro_pesagem"))

    mensagem = ""

    if request.method == "POST":

        placa = request.form.get(
            "placa", ""
        ).strip().upper()

        try:

            peso_bruto = float(
                request.form.get("peso_bruto", "")
            )

            tara = float(
                request.form.get("tara", "")
            )

            if not placa or len(placa) > 7:
                mensagem = "Informe uma placa válida, com até 7 caracteres."

            elif peso_bruto <= 0 or tara < 0:
                mensagem = "Os pesos informados precisam ser valores válidos."

            elif tara >= peso_bruto:
                mensagem = "A tara não pode ser maior ou igual ao peso bruto."

            else:

                pesagem.placa = placa
                pesagem.peso_bruto = peso_bruto
                pesagem.tara = tara
                pesagem.peso_inicial = peso_bruto - tara

                db.session.commit()

                flash("Pesagem atualizada com sucesso.", "sucesso")

                return redirect(url_for("cadastro_pesagem"))

        except (ValueError, TypeError):

            mensagem = "Digite valores numéricos válidos."

    return render_template(
        "editar_pesagem.html",
        pesagem=pesagem,
        mensagem=mensagem
    )


# ==========================================
# GERENCIAMENTO DE USUÁRIOS
# SOMENTE ADMINISTRADOR
# ==========================================

@app.route("/usuarios")
@administrador_obrigatorio
def usuarios():

    lista_usuarios = Usuario.query.order_by(
        Usuario.nome_usuario.asc()
    ).all()

    return render_template(
        "usuarios.html",
        usuarios=lista_usuarios
    )


# ==========================================
# CRIAR NOVO USUÁRIO
# ==========================================

@app.route("/usuarios/criar", methods=["POST"])
@administrador_obrigatorio
def criar_usuario():

    nome_usuario = request.form.get(
        "nome_usuario", ""
    ).strip().lower()

    senha = request.form.get("senha", "")
    tipo = request.form.get("tipo", "")

    if len(nome_usuario) < 3 or len(nome_usuario) > 80:

        flash(
            "O usuário precisa ter entre 3 e 80 caracteres.",
            "erro"
        )

    elif len(senha) < 10:

        flash(
            "A senha precisa ter pelo menos 10 caracteres.",
            "erro"
        )

    elif tipo not in ("administrador", "operador"):

        flash(
            "Selecione um tipo de usuário válido.",
            "erro"
        )

    elif Usuario.query.filter_by(
        nome_usuario=nome_usuario
    ).first():

        flash(
            "Esse nome de usuário já está cadastrado.",
            "erro"
        )

    else:

        novo_usuario = Usuario(
            nome_usuario=nome_usuario,
            senha_hash=generate_password_hash(senha),
            tipo=tipo
        )

        db.session.add(novo_usuario)
        db.session.commit()

        flash("Usuário criado com sucesso.", "sucesso")

    return redirect(url_for("usuarios"))


# ==========================================
# EXCLUIR USUÁRIO
# ==========================================

@app.route("/usuarios/excluir/<int:id>", methods=["POST"])
@administrador_obrigatorio
def excluir_usuario(id):

    usuario = db.session.get(Usuario, id)

    if usuario is None:

        flash("Usuário não encontrado.", "erro")

    elif usuario.id == g.usuario.id:

        flash(
            "Você não pode excluir sua própria conta enquanto estiver conectado.",
            "erro"
        )

    elif usuario.tipo == "administrador" and usuario.ativo:

        quantidade_admins = Usuario.query.filter_by(
            tipo="administrador",
            ativo=True
        ).count()

        if quantidade_admins <= 1:

            flash(
                "O sistema precisa manter pelo menos um administrador ativo.",
                "erro"
            )

        else:

            db.session.delete(usuario)
            db.session.commit()

            flash("Usuário excluído.", "sucesso")

    else:

        db.session.delete(usuario)
        db.session.commit()

        flash("Usuário excluído.", "sucesso")

    return redirect(url_for("usuarios"))


# ==========================================
# CRIAR PRIMEIRO ADMINISTRADOR
# ==========================================

@app.cli.command("criar-admin")
def criar_admin():

    with app.app_context():

        db.create_all()

        nome_usuario = input(
            "Nome de usuário do administrador: "
        ).strip().lower()

        if len(nome_usuario) < 3:

            print("O nome de usuário precisa ter pelo menos 3 caracteres.")
            return

        if Usuario.query.filter_by(
            nome_usuario=nome_usuario
        ).first():

            print("Esse nome de usuário já existe.")
            return

        senha = getpass.getpass(
            "Crie uma senha (mínimo 10 caracteres): "
        )

        confirmacao = getpass.getpass(
            "Digite a senha novamente: "
        )

        if len(senha) < 10:

            print("A senha precisa ter pelo menos 10 caracteres.")
            return

        if senha != confirmacao:

            print("As senhas não conferem.")
            return

        administrador = Usuario(
            nome_usuario=nome_usuario,
            senha_hash=generate_password_hash(senha),
            tipo="administrador"
        )

        db.session.add(administrador)
        db.session.commit()

        print("Administrador criado. Agora entre pelo /login.")


# ==========================================
# ERRO DE MUITAS TENTATIVAS
# ==========================================

@app.errorhandler(429)
def muitas_tentativas(_erro):

    return (
        "Muitas tentativas em pouco tempo. "
        "Aguarde alguns minutos e tente novamente.",
        429
    )


# ==========================================
# EXECUTAR A APLICAÇÃO
# ==========================================

if __name__ == "__main__":

    app.run(
        debug=os.environ.get("FLASK_DEBUG") == "1"
    )