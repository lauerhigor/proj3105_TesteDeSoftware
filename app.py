from flask import Flask, request, redirect, url_for, session
import json
import os
import re
from typing import List, Dict, Tuple, Optional

class ContatoManager:
    def __init__(self, arquivo_json: str):
        self.arquivo_json = arquivo_json

    def ler_dados(self) -> List[Dict[str, str]]:
        """Lê os dados do arquivo JSON e retorna uma lista ordenada de contatos."""
        try:
            if os.path.exists(self.arquivo_json) and os.path.getsize(self.arquivo_json) > 0:
                with open(self.arquivo_json, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    return sorted(dados, key=lambda x: x["nome"].lower())
        except json.JSONDecodeError:
            return []
        return []

    def salvar_dados(self, dados: List[Dict[str, str]]) -> None:
        """Salva a lista de contatos no arquivo JSON."""
        with open(self.arquivo_json, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)

class Validador:
    @staticmethod
    def valida_campo(campo: str) -> Tuple[Optional[str], Optional[str]]:
        """Valida um campo de nome ou sobrenome."""
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

class ContatoController:
    def __init__(self, contato_manager: ContatoManager, validador: Validador):
        self.manager = contato_manager
        self.validador = validador

    def processar_formulario(self, request_form: Dict, session_data: Dict) -> Tuple[Dict, str]:
        """Processa o formulário e retorna os dados atualizados e mensagem de status."""
        dados = self.manager.ler_dados()
        mensagem = ""
        selecionado = -1

        acao = request_form.get("acao")
        if acao == "sair":
            return {}, ""

        nome_input = request_form.get("nome", "").strip()
        sobrenome_input = request_form.get("sobrenome", "").strip()
        genero_input = request_form.get("genero", "")
        index = request_form.get("selecionado", "-1")

        nome, erro1 = self.validador.valida_campo(nome_input)
        sobrenome, erro2 = self.validador.valida_campo(sobrenome_input)

        try:
            selecionado = int(index)
        except ValueError:
            selecionado = -1

        if acao == "inserir":
            if not erro1 and not erro2 and genero_input in ["Masculino", "Feminino", "Outros"]:
                dados.append({"nome": nome, "sobrenome": sobrenome, "genero": genero_input})
                self.manager.salvar_dados(dados)
                return {}, ""
            else:
                mensagem = "Preencha todos os campos corretamente para inserir."
                return {
                    "nome": nome_input,
                    "sobrenome": sobrenome_input,
                    "genero": genero_input,
                    "selecionado": selecionado,
                    "mensagem": mensagem
                }, mensagem

        elif acao == "alterar" and 0 <= selecionado < len(dados):
            if not erro1 and not erro2 and genero_input in ["Masculino", "Feminino", "Outros"]:
                dados[selecionado] = {"nome": nome, "sobrenome": sobrenome, "genero": genero_input}
                self.manager.salvar_dados(dados)
                return {}, ""
            else:
                mensagem = "Preencha todos os campos corretamente para alterar."
                return {
                    "nome": nome_input,
                    "sobrenome": sobrenome_input,
                    "genero": genero_input,
                    "selecionado": selecionado,
                    "mensagem": mensagem
                }, mensagem

        elif acao == "excluir" and 0 <= selecionado < len(dados):
            dados.pop(selecionado)
            self.manager.salvar_dados(dados)
            return {}, ""

        return {}, ""

class TemplateRenderer:
    @staticmethod
    def renderizar_template(dados_contatos: List[Dict[str, str]], 
                          form_data: Dict = None, 
                          mensagem: str = "") -> str:
        """Renderiza o template HTML com os dados fornecidos."""
        nome = form_data.get("nome", "") if form_data else ""
        sobrenome = form_data.get("sobrenome", "") if form_data else ""
        genero = form_data.get("genero", "") if form_data else ""
        selecionado = form_data.get("selecionado", -1) if form_data else -1

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
                .selected {{
                    background-color: #ddf;
                }}
            </style>
            <script>
                function preencherForm(index) {{
                    // Remove a classe 'selected' de todas as linhas
                    document.querySelectorAll('#tabelaContatos tr').forEach(tr => {{
                        tr.classList.remove('selected');
                    }});
                    
                    // Adiciona a classe 'selected' à linha clicada
                    const linha = document.querySelector('#tabelaContatos tr:nth-child(' + (index + 2) + ')');
                    if (linha) linha.classList.add('selected');
                    
                    // Preenche o formulário
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
                <label for="nome">Nome:</label>
                <input type="text" id="nome" name="nome" value="{nome}" required>

                <label for="sobrenome">Sobrenome:</label>
                <input type="text" id="sobrenome" name="sobrenome" value="{sobrenome}" required>

                <label>Gênero:</label>
                <div class="radio-group">
                    <input type="radio" id="genero_Masculino" name="genero" value="Masculino" {"checked" if genero == "Masculino" else ""}>
                    <label for="genero_Masculino">Masculino</label>
                    
                    <input type="radio" id="genero_Feminino" name="genero" value="Feminino" {"checked" if genero == "Feminino" else ""}>
                    <label for="genero_Feminino">Feminino</label>
                    
                    <input type="radio" id="genero_Outros" name="genero" value="Outros" {"checked" if genero == "Outros" else ""}>
                    <label for="genero_Outros">Outros</label>
                </div>

                <input type="hidden" name="selecionado" id="selecionado" value="{selecionado}">
                
                <div>
                    <button type="submit" class="btn" name="acao" value="inserir">Inserir dados</button>
                    <button type="submit" class="btn" name="acao" value="alterar">Editar registro</button>
                    <button type="submit" class="btn" name="acao" value="excluir">Excluir registro</button>
                    <button type="button" class="btn" onclick="fecharJanela()">Sair</button>
                </div>
            </form>

            {f'<p class="mensagem">{mensagem}</p>' if mensagem else ''}

            <div style="width:95%; max-width:800px; margin-bottom:10px;">
                <label for="filtro">Buscar por nome:</label>
                <input type="text" id="filtro" onkeyup="filtrarTabela()" placeholder="Digite para buscar..." style="width:100%; padding:8px;">
            </div>

            <h3>Lista de Contatos:</h3>
            <div class="tabela-container">
                <table id="tabelaContatos">
                    <thead>
                        <tr>
                            <th>Nome</th>
                            <th>Sobrenome</th>
                            <th>Gênero</th>
                        </tr>
                    </thead>
                    <tbody>"""

        for i, p in enumerate(dados_contatos):
            html += f"""
                        <tr onclick="preencherForm({i})" {"class='selected'" if i == selecionado else ""}>
                            <td id="nome_{i}">{p['nome']}</td>
                            <td id="sobrenome_{i}">{p['sobrenome']}</td>
                            <td id="genero_{i}">{p['genero']}</td>
                        </tr>"""

        html += """
                    </tbody>
                </table>
            </div>
        </body>
        </html>"""

        return html

def create_app():
    """Factory function para criar a aplicação Flask."""
    app = Flask(__name__)
    app.secret_key = "secreto_para_sessao"

    # Configuração dos componentes
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ARQUIVO_JSON = os.path.join(BASE_DIR, "cadastro.json")
    
    contato_manager = ContatoManager(ARQUIVO_JSON)
    validador = Validador()
    controller = ContatoController(contato_manager, validador)
    renderer = TemplateRenderer()

    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "POST":
            form_data, mensagem = controller.processar_formulario(request.form, session)
            if mensagem:
                session.update(form_data)
                session["mensagem"] = mensagem
                return redirect(url_for("index"))
            return redirect(url_for("index"))

        dados = contato_manager.ler_dados()
        mensagem = session.pop("mensagem", "")
        form_data = {
            "nome": session.pop("nome", ""),
            "sobrenome": session.pop("sobrenome", ""),
            "genero": session.pop("genero", ""),
            "selecionado": session.pop("selecionado", -1)
        }

        return renderer.renderizar_template(dados, form_data, mensagem)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
