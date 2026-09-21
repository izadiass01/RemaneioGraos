# 🌾 Remaneio de Grãos

🌐 **Sistema online:** https://izabellydias17.pythonanywhere.com/

## 📌 Sobre o projeto

O **Remaneio de Grãos** é um sistema desenvolvido para auxiliar no registro e controle da pesagem de caminhões durante o recebimento de grãos.

O sistema permite cadastrar os dados da pesagem, calcular o peso inicial, visualizar os registros e também editar ou excluir uma pesagem.

## 🎯 Objetivo

Facilitar o registro das informações de pesagem dos caminhões e organizar os dados de forma simples e prática.

## ⚙️ Funcionalidades

- Cadastro da placa do caminhão;
- Registro do peso bruto;
- Registro da tara;
- Cálculo automático do peso inicial;
- Registro da data e hora;
- Listagem das pesagens;
- Edição de pesagens;
- Exclusão de pesagens;
- Armazenamento dos dados em banco SQLite.

## 💻 Tecnologias utilizadas

- Python
- Flask
- SQLite
- SQLAlchemy
- HTML5
- CSS3
- Git
- GitHub
- PythonAnywhere

## 🗂️ Estrutura do projeto

```text
RemaneioGraos/
├── app.py
├── requirements.txt
├── remaneio.db
├── templates/
│   ├── index.html
│   ├── cadastro_pesagem.html
│   └── editar_pesagem.html
├── static/
│   └── style.css
└── .gitignore