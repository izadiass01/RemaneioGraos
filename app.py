
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# Caminho da pasta do projeto
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Configuração do banco SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///" + os.path.join(BASE_DIR, "remaneio.db")
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ==========================================================
# MODELO DO BANCO DE DADOS
# ==========================================================

class Pesagem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    placa = db.Column(db.String(20), nullable=False)
    peso_bruto = db.Column(db.Float, nullable=False)
    tara = db.Column(db.Float, nullable=False)
    peso_inicial = db.Column(db.Float, nullable=False)
    data_hora = db.Column(db.String(20), nullable=False)


# Cria o banco e a tabela automaticamente
with app.app_context():
    db.create_all()


# ==========================================================
# PÁGINA INICIAL
# ==========================================================

@app.route("/")
def index():
    return render_template("index.html")


# ==========================================================
# CADASTRO DE PESAGEM
# ==========================================================

@app.route("/cadastro-pesagem", methods=["GET", "POST"])
def cadastro_pesagem():

    mensagem = ""

    if request.method == "POST":

        placa = request.form.get("placa")
        peso_bruto = request.form.get("peso_bruto")
        tara = request.form.get("tara")

        try:
            peso_bruto = float(peso_bruto)
            tara = float(tara)

            if peso_bruto <= 0 or tara < 0:

                mensagem = "Os pesos informados precisam ser valores válidos."

            elif tara >= peso_bruto:

                mensagem = "A tara não pode ser maior ou igual ao peso bruto."

            elif not placa:

                mensagem = "Informe a placa do caminhão."

            else:

                # Cálculo do peso líquido
                peso_inicial = peso_bruto - tara

                # Data e hora do registro
                data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")

                # Cria uma nova pesagem
                nova_pesagem = Pesagem(
                    placa=placa.upper(),
                    peso_bruto=peso_bruto,
                    tara=tara,
                    peso_inicial=peso_inicial,
                    data_hora=data_hora
                )

                # Salva no banco
                db.session.add(nova_pesagem)
                db.session.commit()

                mensagem = "Pesagem registrada com sucesso!"

        except (ValueError, TypeError):

            mensagem = "Digite valores numéricos válidos."

    # Busca todas as pesagens no banco
    pesagens = Pesagem.query.order_by(Pesagem.id.desc()).all()

    return render_template(
        "cadastro_pesagem.html",
        pesagens=pesagens,
        mensagem=mensagem
    )


# ==========================================================
# EXCLUIR UMA PESAGEM
# ==========================================================

@app.route("/excluir/<int:id>", methods=["POST"])
def excluir(id):

    pesagem = db.session.get(Pesagem, id)

    if pesagem:
        db.session.delete(pesagem)
        db.session.commit()

    return redirect(url_for("cadastro_pesagem"))


# ==========================================================
# ABRIR PÁGINA DE EDIÇÃO
# ==========================================================

@app.route("/editar/<int:id>", methods=["GET"])
def editar(id):

    pesagem = db.session.get(Pesagem, id)

    if pesagem is None:
        return redirect(url_for("cadastro_pesagem"))

    return render_template(
        "editar_pesagem.html",
        pesagem=pesagem
    )


# ==========================================================
# SALVAR EDIÇÃO
# ==========================================================

@app.route("/editar/<int:id>", methods=["POST"])
def salvar_edicao(id):

    pesagem = db.session.get(Pesagem, id)

    if pesagem is None:
        return redirect(url_for("cadastro_pesagem"))

    placa = request.form.get("placa")
    peso_bruto = request.form.get("peso_bruto")
    tara = request.form.get("tara")

    try:

        peso_bruto = float(peso_bruto)
        tara = float(tara)

        dados_pesagem = {
            "id": id,
            "placa": placa,
            "peso_bruto": peso_bruto,
            "tara": tara
        }

        if not placa:

            return render_template(
                "editar_pesagem.html",
                pesagem=dados_pesagem,
                mensagem="Informe a placa do caminhão."
            )

        if peso_bruto <= 0 or tara < 0:

            return render_template(
                "editar_pesagem.html",
                pesagem=dados_pesagem,
                mensagem="Os pesos informados precisam ser valores válidos."
            )

        if tara >= peso_bruto:

            return render_template(
                "editar_pesagem.html",
                pesagem=dados_pesagem,
                mensagem="A tara não pode ser maior ou igual ao peso bruto."
            )

        # Atualiza os dados
        pesagem.placa = placa.upper()
        pesagem.peso_bruto = peso_bruto
        pesagem.tara = tara
        pesagem.peso_inicial = peso_bruto - tara

        db.session.commit()

        return redirect(url_for("cadastro_pesagem"))

    except (ValueError, TypeError):

        return render_template(
            "editar_pesagem.html",
            pesagem={
                "id": id,
                "placa": placa,
                "peso_bruto": peso_bruto,
                "tara": tara
            },
            mensagem="Digite valores numéricos válidos."
        )


# ==========================================================
# EXECUÇÃO LOCAL
# ==========================================================

if __name__ == "__main__":
    app.run(debug=True)
