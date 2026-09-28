from flask import Flask, render_template, request

app = Flask(__name__)


def calcular_peso_liquido_real(peso_bruto, tara, desconto_umidade, desconto_impurezas):

    if peso_bruto is None or tara is None:
        raise ValueError("Peso bruto e tara são obrigatórios.")

    if desconto_umidade is None or desconto_impurezas is None:
        raise ValueError("Os descontos de umidade e impurezas são obrigatórios.")

    peso_inicial = peso_bruto - tara

    desconto_total = desconto_umidade + desconto_impurezas

    peso_liquido_real = peso_inicial - desconto_total

    return max(peso_liquido_real, 0)


@app.route("/", methods=["GET", "POST"])
def inicio():

    resultado = None
    erro = None

    dados = {
        "peso_bruto": "",
        "tara": "",
        "desconto_umidade": "",
        "desconto_impurezas": ""
    }

    if request.method == "POST":

        try:
            dados["peso_bruto"] = request.form.get("peso_bruto")
            dados["tara"] = request.form.get("tara")
            dados["desconto_umidade"] = request.form.get("desconto_umidade")
            dados["desconto_impurezas"] = request.form.get("desconto_impurezas")

            peso_bruto = float(dados["peso_bruto"])
            tara = float(dados["tara"])
            desconto_umidade = float(dados["desconto_umidade"])
            desconto_impurezas = float(dados["desconto_impurezas"])

            if peso_bruto < 0 or tara < 0:
                raise ValueError("Os pesos não podem ser negativos.")

            if desconto_umidade < 0 or desconto_impurezas < 0:
                raise ValueError("Os descontos não podem ser negativos.")

            if tara > peso_bruto:
                raise ValueError("A tara não pode ser maior que o peso bruto.")

            resultado = calcular_peso_liquido_real(
                peso_bruto,
                tara,
                desconto_umidade,
                desconto_impurezas
            )

        except ValueError as e:
            erro = str(e)

        except Exception:
            erro = "Preencha todos os campos corretamente."

    return render_template(
        "index.html",
        resultado=resultado,
        erro=erro,
        dados=dados
    )


if __name__ == "__main__":
    app.run(debug=True)