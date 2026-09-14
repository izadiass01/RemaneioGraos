from flask import Flask, render_template, request
from datetime import datetime

app = Flask(__name__)

pesagens = []


@app.route("/")
def index():
    return render_template("index.html")


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
                peso_inicial = peso_bruto - tara

                data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")

                nova_pesagem = {
                    "placa": placa.upper(),
                    "peso_bruto": peso_bruto,
                    "tara": tara,
                    "peso_inicial": peso_inicial,
                    "data_hora": data_hora
                }

                pesagens.append(nova_pesagem)

                mensagem = "Pesagem registrada com sucesso!"

        except (ValueError, TypeError):
            mensagem = "Digite valores numéricos válidos."

    return render_template(
        "cadastro_pesagem.html",
        pesagens=pesagens,
        mensagem=mensagem
    )


if __name__ == "__main__":
    app.run(debug=True)