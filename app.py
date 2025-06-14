from flask import Flask, request, redirect, url_for, session
import json
import os
import re

# --------------------- Caminho multiplataforma ---------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_JSON = os.path.join(BASE_DIR, "cadastro.json")

# --------------------- Validação de campos (função auxiliar) ---------------------
def validate_field(field):
    if not field:
        return None, 
    if len(field) > 50:
        return None, 
    if not re.match(r"^[A-Za-z\sà-üÀ-Ü]{1,50}$", field):
        return None, 

    prepositions = ["da", "de", "do", "das", "dos"]
    formatted_field = " ".join([
        part.capitalize() if part.lower() not in prepositions else part.lower()
        for part in re.sub(r"\s+", " ", field).strip().split()
    ])
    return formatted_field, None

class Contact:
    def __init__(self, nome, sobrenome, genero):
        self.nome = nome
        self.sobrenome = sobrenome
        self.genero = genero

    def to_dict(self):
        return {
            "nome": self.nome,
            "sobrenome": self.sobrenome,
            "genero": self.genero
        }

class ContactManager:
    def __init__(self, json_file_path):
        self.json_file_path = json_file_path
        self._ensure_json_file_exists()

    def _ensure_json_file_exists(self):
        if not os.path.exists(self.json_file_path):
            with open(self.json_file_path, "w", encoding="utf-8") as f:
                json.dump([], f)
        elif os.path.getsize(self.json_file_path) == 0:
            with open(self.json_file_path, "w", encoding="utf-8") as f:
                json.dump([], f) 

    def _read_data(self):
        try:
            with open(self.json_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    return []
                return [Contact(**item) for item in data if isinstance(item, dict)]
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_data(self, contacts):
        data_to_save = [contact.to_dict() for contact in contacts]
        with open(self.json_file_path, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=4, ensure_ascii=False)

    def get_all_contacts(self):
        contacts = self._read_data()
        return sorted(contacts, key=lambda x: x.nome.lower())

    def add_contact(self, contact):
        contacts = self._read_data()
        contacts.append(contact)
        self._save_data(contacts)

    def update_contact(self, index, new_contact):
        contacts = self._read_data()
        if 0 <= index < len(contacts):
            contacts[index] = new_contact
            self._save_data(contacts)
            return True
        return False

    def delete_contact(self, index):
        contacts = self._read_data()
        if 0 <= index < len(contacts):
            del contacts[index]
            self._save_data(contacts)
            return True
        return False

class ContactApp:
    def __init__(self, secret_key, json_file_path):
        self.app = Flask(__name__)
        self.app.secret_key = secret_key
        self.contact_manager = ContactManager(json_file_path)
        self.setup_routes()

    def setup_routes(self):
        self.app.add_url_rule("/", "index", self.index, methods=["GET", "POST"])

    def _render_html(self, contacts, mensagem, nome_input, sobrenome_input, genero_input, selecionado):
        html_rows = ""
        for i, p in enumerate(contacts):
            html_rows += f"""
                <tr onclick="preencherForm({i})">
                    <td id="nome_{i}">{p.nome}</td>
                    <td id="sobrenome_{i}">{p.sobrenome}</td>
                    <td id="genero_{i}">{p.genero}</td>
                </tr>"""

        return f"""
        <!DOCTYPE html>
        <html lang="pt-br">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Cadastro de Contatos</title>
            <style>
                body {{
                    font-family: 'Inter', sans-serif;
                    background-color: #f0f4f8;
                    padding: 20px;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                }}
                form, .tabela-container, .search-container {{
                    background-color: #ffffff;
                    padding: 25px;
                    border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                    width: 95%;
                    max-width: 800px;
                    margin-bottom: 25px;
                    border: 1px solid #e0e6ed;
                }}
                h2, h3 {{
                    color: #2c3e50;
                    margin-bottom: 20px;
                    font-weight: 600;
                }}
                label {{
                    font-weight: 600;
                    display: block;
                    margin-bottom: 8px;
                    color: #34495e;
                }}
                input[type="text"] {{
                    width: calc(100% - 20px);
                    padding: 10px;
                    margin-bottom: 15px;
                    border: 1px solid #ced4da;
                    border-radius: 6px;
                    font-size: 16px;
                    transition: border-color 0.3s ease;
                }}
                input[type="text"]:focus {{
                    border-color: #4CAF50;
                    outline: none;
                }}
                .radio-group {{
                    margin-bottom: 20px;
                    display: flex;
                    gap: 15px;
                }}
                .radio-group input[type="radio"] {{
                    margin-right: 5px;
                }}
                .radio-group label {{
                    font-weight: normal;
                    display: inline-block;
                    margin-right: 5px;
                    cursor: pointer;
                }}
                .btn {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 12px 22px;
                    margin-top: 15px;
                    margin-right: 12px;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 16px;
                    font-weight: 500;
                    transition: background-color 0.3s ease, transform 0.2s ease, box-shadow 0.3s ease;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }}
                .btn:hover {{
                    background-color: #45a049;
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                }}
                .btn:active {{
                    transform: translateY(0);
                    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
                }}
                .btn-exit {{
                    background-color: #f44336;
                }}
                .btn-exit:hover {{
                    background-color: #da190b;
                }}
                .mensagem {{
                    color: #d32f2f;
                    font-weight: bold;
                    margin-bottom: 20px;
                    text-align: center;
                }}
                .search-container {{
                    padding: 15px 25px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                th, td {{
                    border: 1px solid #dee2e6;
                    padding: 12px;
                    text-align: left;
                    font-size: 15px;
                }}
                th {{
                    background-color: #e9ecef;
                    color: #495057;
                    position: sticky;
                    top: 0;
                    z-index: 1;
                }}
                tr:nth-child(even) {{
                    background-color: #f8f9fa;
                }}
                tr:hover {{
                    background-color: #e2f2e5;
                    cursor: pointer;
                }}
                .tabela-container {{
                    max-height: 350px;
                    overflow-y: auto;
                }}
            </style>
            <script>
                function preencherForm(index) {{
                    document.getElementById("nome").value = document.getElementById("nome_" + index).textContent;
                    document.getElementById("sobrenome").value = document.getElementById("sobrenome_" + index).textContent;
                    const genero = document.getElementById("genero_" + index).textContent;
                    // Define o radio button de gênero baseado no valor da célula da tabela
                    const radio = document.getElementById("genero_" + genero);
                    if (radio) radio.checked = true;
                    document.getElementById("selecionado").value = index;
                }}

                function filtrarTabela() {{
                    let filtro = document.getElementById("filtro").value.toLowerCase();
                    let linhas = document.querySelectorAll("#tabelaContatos tbody tr"); // Seleciona apenas as linhas do corpo da tabela
                    linhas.forEach((linha) => {{
                        let nome = linha.cells[0].innerText.toLowerCase();
                        let sobrenome = linha.cells[1].innerText.toLowerCase();
                        // Mostra ou esconde a linha com base no filtro
                        linha.style.display = (nome.includes(filtro) || sobrenome.includes(filtro)) ? "" : "none";
                    }});
                }}

                // Devido a restrições de segurança do navegador, window.close() só funciona
                // para janelas abertas pelo próprio script. Neste ambiente, não é garantido.
                // Recomenda-se que o usuário feche a aba manualmente.
                function fecharJanela() {{
                    console.log("Para sair, feche esta aba ou janela do navegador manualmente.");
                    // window.close(); // Esta linha foi removida pois não funciona de forma confiável
                    // setTimeout(() => {{ alert(...) }}); // alert() não é permitido neste ambiente.
                }}
            </script>
        </head>
        <body>
            <h2>Cadastro de Contatos</h2>

            <form method="POST">
                <label for="nome">Nome:</label>
                <input type="text" name="nome" id="nome" value="{nome_input}" required>

                <label for="sobrenome">Sobrenome:</label>
                <input type="text" name="sobrenome" id="sobrenome" value="{sobrenome_input}" required>

                <label>Gênero:</label>
                <div class="radio-group">
                    <input type="radio" name="genero" id="genero_Masculino" value="Masculino" {"checked" if genero_input == "Masculino" else ""}>
                    <label for="genero_Masculino">Masculino</label>
                    <input type="radio" name="genero" id="genero_Feminino" value="Feminino" {"checked" if genero_input == "Feminino" else ""}>
                    <label for="genero_Feminino">Feminino</label>
                    <input type="radio" name="genero" id="genero_Outros" value="Outros" {"checked" if genero_input == "Outros" else ""}>
                    <label for="genero_Outros">Outros</label>
                </div>

                <input type="hidden" name="selecionado" id="selecionado" value="{selecionado}">
                <div>
                    <button class="btn" name="acao" value="inserir">Inserir dados</button>
                    <button class="btn" name="acao" value="alterar">Editar registro</button>
                    <button class="btn btn-exit" name="acao" value="excluir">Excluir registro</button>
                    <button type="button" class="btn btn-exit" onclick="fecharJanela()">Sair</button>
                </div>
            </form>

            {"<p class='mensagem'>" + mensagem + "</p>" if mensagem else ""}

            <div class="search-container">
                <label for="filtro">Buscar por nome:</label>
                <input type="text" id="filtro" onkeyup="filtrarTabela()" placeholder="Digite para buscar...">
            </div>

            <h3>Lista de Contatos:</h3>
            <div class="tabela-container">
            <table id="tabelaContatos">
                <thead>
                    <tr><th>Nome</th><th>Sobrenome</th><th>Gênero</th></tr>
                </thead>
                <tbody>
                    {html_rows}
                </tbody>
            </table>
            </div>
        </body>
        </html>"""

    def index(self):
        contacts = self.contact_manager.get_all_contacts()
        mensagem = session.pop("mensagem", "")
        selecionado = session.pop("selecionado", -1)
        nome_input = session.pop("nome", "")
        sobrenome_input = session.pop("sobrenome", "")
        genero_input = session.pop("genero", "")

        if request.method == "POST":
            acao = request.form.get("acao")
            if acao == "sair":
                return redirect(url_for("index"))

            nome_form = request.form.get("nome", "").strip()
            sobrenome_form = request.form.get("sobrenome", "").strip()
            genero_form = request.form.get("genero", "")
            index_str = request.form.get("selecionado", "-1")
            nome_validado, erro1 = validate_field(nome_form)
            sobrenome_validado, erro2 = validate_field(sobrenome_form)

            try:
                selecionado = int(index_str)
            except ValueError:
                selecionado = -1

            if acao == "inserir":
                if not erro1 and not erro2 and genero_form in ["Masculino", "Feminino", "Outros"]:
                    new_contact = Contact(nome_validado, sobrenome_validado, genero_form)
                    self.contact_manager.add_contact(new_contact)
                    return redirect(url_for("index"))
                else:
                    session["mensagem"] = "Preencha todos os campos corretamente para inserir."
                    session["nome"] = nome_form
                    session["sobrenome"] = sobrenome_form
                    session["genero"] = genero_form
                    session["selecionado"] = selecionado
                    return redirect(url_for("index"))

            elif acao == "alterar":
                if 0 <= selecionado < len(contacts) and not erro1 and not erro2 and genero_form in ["Masculino", "Feminino", "Outros"]:
                    updated_contact = Contact(nome_validado, sobrenome_validado, genero_form)
                    self.contact_manager.update_contact(selecionado, updated_contact)
                    return redirect(url_for("index"))
                else:
                    session["mensagem"] = "Preencha todos os campos corretamente para alterar."
                    session["nome"] = nome_form
                    session["sobrenome"] = sobrenome_form
                    session["genero"] = genero_form
                    session["selecionado"] = selecionado
                    return redirect(url_for("index"))

            elif acao == "excluir":
                if 0 <= selecionado < len(contacts):
                    self.contact_manager.delete_contact(selecionado)
                    return redirect(url_for("index"))
        contacts = self.contact_manager.get_all_contacts()
        return self._render_html(contacts, mensagem, nome_input, sobrenome_input, genero_input, selecionado)

    def run(self, debug=True):
        self.app.run(debug=debug)

if __name__ == "__main__":
    app_instance = ContactApp(
        secret_key="secreto_para_sessao",
        json_file_path=ARQUIVO_JSON 
    )
    app_instance.run()
