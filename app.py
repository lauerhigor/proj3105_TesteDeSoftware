from flask import Flask, request, redirect, url_for, session
import json
import os
import re

app = Flask(__name__)
app.secret_key = "secreto_para_sessao"

# --------------------- Caminho multiplataforma ---------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_JSON = os.path.join(BASE_DIR, "cadastro.json")

# --------------------- Validação de campos ---------------------
def valida_campo(campo):
    if not campo:
        return None, "Campo vazio."
    if len(campo) > 50:
        return None, "Campo muito longo."
    if not re.match(r"^[A-Za-z\sà-ü]{1,50}$", campo):
        return None, "Caracteres inválidos."
    preposicoes = ["da", "de", "do", "das", "dos"]
    campo_formatado = " ".join([
        parte.capitalize() if parte not in preposicoes else parte
        for parte in re.sub(r"\s+", " ", campo).split()
    ])
    return campo_formatado, None

# --------------------- JSON ---------------------
def ler_dados():
    try:
        if os.path.exists(ARQUIVO_JSON) and os.path.getsize(ARQUIVO_JSON) > 0:
            with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
                dados = json.load(f)
                return sorted(dados, key=lambda x: x["nome"].lower())
    except json.JSONDecodeError:
        return []
    return []

def salvar_dados(dados):
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# --------------------- Página principal ---------------------
@app.route("/", methods=["GET", "POST"])
def index():
    dados = ler_dados()
    mensagem = session.pop("mensagem", "")
    selecionado = -1
    nome = ""
    sobrenome = ""
    genero = ""

    if request.method == "POST":
        acao = request.form.get("acao")
        if acao == "sair":
            return redirect(url_for("index"))  # JavaScript lida com o fechamento da aba

        nome_input = request.form.get("nome", "").strip()
        sobrenome_input = request.form.get("sobrenome", "").strip()
        genero_input = request.form.get("genero", "")
        index = request.form.get("selecionado", "-1")

        nome, erro1 = valida_campo(nome_input)
        sobrenome, erro2 = valida_campo(sobrenome_input)

        try:
            selecionado = int(index)
        except:
            selecionado = -1

        if acao == "inserir":
            if not erro1 and not erro2 and genero_input in ["Masculino", "Feminino", "Outros"]:
                dados.append({"nome": nome, "sobrenome": sobrenome, "genero": genero_input})
                salvar_dados(dados)
                return redirect(url_for("index"))
            else:
                session["mensagem"] = "Preencha todos os campos corretamente para inserir."
                session["nome"] = nome_input
                session["sobrenome"] = sobrenome_input
                session["genero"] = genero_input
                session["selecionado"] = selecionado
                return redirect(url_for("index"))

        elif acao == "alterar" and 0 <= selecionado < len(dados):
            if not erro1 and not erro2 and genero_input in ["Masculino", "Feminino", "Outros"]:
                dados[selecionado] = {"nome": nome, "sobrenome": sobrenome, "genero": genero_input}
                salvar_dados(dados)
                return redirect(url_for("index"))
            else:
                session["mensagem"] = "Preencha todos os campos corretamente para alterar."
                session["nome"] = nome_input
                session["sobrenome"] = sobrenome_input
                session["genero"] = genero_input
                session["selecionado"] = selecionado
                return redirect(url_for("index"))

        elif acao == "excluir" and 0 <= selecionado < len(dados):
            dados.pop(selecionado)
            salvar_dados(dados)
            return redirect(url_for("index"))

    nome = session.pop("nome", "")
    sobrenome = session.pop("sobrenome", "")
    genero = session.pop("genero", "")
    selecionado = session.pop("selecionado", -1)

    # --------------------- HTML embutido ---------------------
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>Cadastro de Contatos</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f2f2f2;
                padding: 20px;
                display: flex;
                flex-direction: column;
                align-items: center;
            }}
            form {{
                background-color: #fff;
                padding: 20px;
                border-radius: 8px;
                width: 95%;
                max-width: 800px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }}
            label {{
                font-weight: bold;
                display: block;
                margin-top: 10px;
            }}
            input[type="text"] {{
                width: 100%;
                padding: 8px;
                margin-top: 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }}
            .radio-group {{
                margin-top: 10px;
            }}
            .radio-group input {{
                margin-left: 10px;
                margin-right: 5px;
            }}
            .btn {{
                background-color: #4CAF50;
                color: white;
                padding: 10px 15px;
                margin-top: 15px;
                margin-right: 10px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            }}
            .mensagem {{
                color: red;
                font-weight: bold;
                margin-bottom: 15px;
            }}
            .tabela-container {{
                width: 95%;
                max-width: 800px;
                max-height: 300px;
                overflow-y: auto;
                border: 1px solid #ccc;
                border-radius: 8px;
                background-color: white;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                border: 1px solid #aaa;
                padding: 10px;
                text-align: left;
            }}
            th {{
                background-color: #ddd;
                position: sticky;
                top: 0;
            }}
            tr:hover {{
                background-color: #eef;
                cursor: pointer;
            }}
        </style>
        <script>
            function preencherForm(index) {{
                document.getElementById("nome").value = document.getElementById("nome_" + index).textContent;
                document.getElementById("sobrenome").value = document.getElementById("sobrenome_" + index).textContent;
                const genero = document.getElementById("genero_" + index).textContent;
                const radio = document.getElementById("genero_" + genero);
                if (radio) radio.checked = true;
                document.getElementById("selecionado").value = index;
            }}

            function filtrarTabela() {{
                let filtro = document.getElementById("filtro").value.toLowerCase();
                let linhas = document.querySelectorAll("#tabelaContatos tr");
                linhas.forEach((linha, i) => {{
                    if (i === 0) return;
                    let nome = linha.cells[0].innerText.toLowerCase();
                    let sobrenome = linha.cells[1].innerText.toLowerCase();
                    linha.style.display = nome.includes(filtro) || sobrenome.includes(filtro) ? "" : "none";
                }});
            }}

            function fecharJanela() {{
                window.close();
                setTimeout(() => {{
                    alert("Se a aba não foi fechada automaticamente, feche-a manualmente.");
                }}, 300);
            }}
        </script>
    </head>
    <body>
        <h2>Cadastro de Contatos</h2>

        <form method="POST">
            <label>Nome:</label>
            <input type="text" name="nome" id="nome" value="{nome}" required>

            <label>Sobrenome:</label>
            <input type="text" name="sobrenome" id="sobrenome" value="{sobrenome}" required>

            <label>Gênero:</label>
            <div class="radio-group">
                <input type="radio" name="genero" id="genero_Masculino" value="Masculino" {"checked" if genero == "Masculino" else ""}>Masculino
                <input type="radio" name="genero" id="genero_Feminino" value="Feminino" {"checked" if genero == "Feminino" else ""}>Feminino
                <input type="radio" name="genero" id="genero_Outros" value="Outros" {"checked" if genero == "Outros" else ""}>Outros
            </div>

            <input type="hidden" name="selecionado" id="selecionado" value="{selecionado}">
            <div>
                <button class="btn" name="acao" value="inserir">Inserir dados</button>
                <button class="btn" name="acao" value="alterar">Editar registro</button>
                <button class="btn" name="acao" value="excluir">Excluir registro</button>
                <button type="button" class="btn" onclick="fecharJanela()">Sair</button>
            </div>
        </form>

        <p class="mensagem">{mensagem}</p>

        <div style="width:95%; max-width:800px; margin-bottom:10px;">
            <label>Buscar por nome:</label>
            <input type="text" id="filtro" onkeyup="filtrarTabela()" placeholder="Digite para buscar..." style="width:100%; padding:8px;">
        </div>

        <h3>Lista de Contatos:</h3>
        <div class="tabela-container">
        <table id="tabelaContatos">
            <tr><th>Nome</th><th>Sobrenome</th><th>Gênero</th></tr>"""

    for i, p in enumerate(ler_dados()):
        html += f"""
            <tr onclick="preencherForm({i})">
                <td id="nome_{i}">{p['nome']}</td>
                <td id="sobrenome_{i}">{p['sobrenome']}</td>
                <td id="genero_{i}">{p['genero']}</td>
            </tr>"""

    html += """
        </table>
        </div>
    </body>
    </html>"""

    return html

if __name__ == "__main__":
    app.run(debug=True)
