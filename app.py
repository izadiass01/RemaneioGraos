from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/")
def inicio():
    return render_template("cadastro.html")


@app.route("/calcular", methods=["POST"])
def calcular():
    peso_bruto = float(request.form["peso_bruto"])
    tara = float(request.form["tara"])
    umidade = float(request.form["umidade"])
    impurezas = float(request.form["impurezas"])

    # Validação dos dados
    if peso_bruto <= 0:
        return "Erro: o peso bruto deve ser maior que zero."

    if tara < 0:
        return "Erro: a tara não pode ser negativa."

    if tara >= peso_bruto:
        return "Erro: a tara deve ser menor que o peso bruto."

    if umidade < 0 or umidade > 100:
        return "Erro: a umidade deve estar entre 0% e 100%."

    if impurezas < 0 or impurezas > 100:
        return "Erro: as impurezas devem estar entre 0% e 100%."

    # Calcula o peso líquido
    peso_liquido = peso_bruto - tara

    # Calcula os descontos
    desconto_umidade = peso_liquido * (umidade / 100)
    desconto_impurezas = peso_liquido * (impurezas / 100)

    # Calcula o peso final
    peso_final = (
        peso_liquido
        - desconto_umidade
        - desconto_impurezas
    )

    return render_template(
        "resultado.html",
        peso_liquido=peso_liquido,
        desconto_umidade=desconto_umidade,
        impurezas=desconto_impurezas,
        peso_final=peso_final
    )


if __name__ == "__main__":
    app.run(debug=True)