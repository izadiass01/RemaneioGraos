def calcular_peso_liquido_real(peso_bruto, tara, desconto_umidade, desconto_impurezas):
   
    if peso_bruto is None or tara is None:
        raise ValueError("Peso bruto e tara são obrigatórios.")

    if desconto_umidade is None or desconto_impurezas is None:
        raise ValueError("Os descontos de umidade e impurezas são obrigatórios.")
  
    peso_inicial = peso_bruto - tara
  
    desconto_total = desconto_umidade + desconto_impurezas
   
    peso_liquido_real = peso_inicial - desconto_total

    return max(peso_liquido_real, 0)

print("Teste 1 - Cálculo normal:")
resultado = calcular_peso_liquido_real(10000, 2000, 300, 100)
print(f"Resultado: {resultado} kg")

print("\nTeste 2 - Informação faltando:")
try:
    resultado = calcular_peso_liquido_real(10000, 2000, None, 100)
    print(f"Resultado: {resultado} kg")
except ValueError as erro:
    print(f"Erro esperado: {erro}")

print("\nTeste 3 - Resultado negativo:")
resultado = calcular_peso_liquido_real(1000, 900, 300, 100)
print(f"Resultado: {resultado} kg")
