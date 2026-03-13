from flask import Flask, request, redirect, session, url_for
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "vibe_store_seguro_2026"

# --- CONFIGURAÇÃO DO BANCO DE DATOS SQLITE ---
DB_NAME = "vibe_store.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS produtos (
        codigo TEXT PRIMARY KEY, nome TEXT, cor TEXT, preco REAL,
        P INTEGER, M INTEGER, G INTEGER, GG INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, total REAL, 
        pagamento TEXT, cliente TEXT, parcelas TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS caixa (
        metodo TEXT PRIMARY KEY, valor REAL)''')
    for metodo in ["Dinheiro", "Pix", "Cartão", "A prazo"]:
        cursor.execute("INSERT OR IGNORE INTO caixa VALUES (?, ?)", (metodo, 0.0))
    conn.commit()
    conn.close()

init_db()

def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

USUARIOS = {"admin": {"senha": "123", "nivel": "total"}, "vendedor": {"senha": "456", "nivel": "vendas"}}

# --- ROTAS DE LOGIN E PAINEL (MANTIDAS) ---
@app.route("/")
def login():
    return '''<div style="font-family:sans-serif; max-width:300px; margin:100px auto; border:1px solid #ccc; padding:20px; border-radius:10px;">
        <h2 style="text-align:center;">VIBE STORE</h2>
        <form method="post" action="/logar">
            Usuário<br><input name="usuario" style="width:100%; margin-bottom:10px;"><br>
            Senha<br><input type="password" name="senha" style="width:100%; margin-bottom:20px;"><br>
            <button style="width:100%; padding:10px; background:#000; color:#fff; border:none; cursor:pointer;">Entrar</button>
        </form></div>'''

@app.route("/logar", methods=["POST"])
def logar():
    u, s = request.form.get("usuario"), request.form.get("senha")
    if u in USUARIOS and USUARIOS[u]["senha"] == s:
        session.update({"usuario": u, "nivel": USUARIOS[u]["nivel"], "carrinho": []})
        return redirect("/painel")
    return "Erro! <a href='/'>Tentar novamente</a>"

@app.route("/painel")
def painel():
    if "usuario" not in session: return redirect("/")
    vendas_db = query_db("SELECT SUM(total) as faturamento FROM vendas", one=True)
    faturamento = vendas_db['faturamento'] if vendas_db['faturamento'] else 0
    return f'''<div style="font-family:sans-serif; padding:20px;">
        <h1>VIBE STORE</h1>
        <p>Usuário: <b>{session['usuario']}</b> | <a href="/logout">Sair</a></p>
        <div style="background:#f0f0f0; padding:15px; border-radius:10px; margin-bottom:20px;">
            <b>Faturamento: R$ {faturamento:.2f}</b>
        </div>
        <div style="display:flex; gap:10px; flex-wrap:wrap;">
            <a href="/vender" style="padding:15px; background:green; color:white; text-decoration:none; border-radius:5px;">🛒 NOVA VENDA</a>
            {"<a href='/estoque' style='padding:15px; background:blue; color:white; text-decoration:none; border-radius:5px;'>📦 ESTOQUE</a>" if session['nivel']=='total' else ""}
            <a href="/caixa" style="padding:15px; background:#555; color:white; text-decoration:none; border-radius:5px;">💰 CAIXA</a>
            <a href="/historico" style="padding:15px; background:#555; color:white; text-decoration:none; border-radius:5px;">📄 HISTÓRICO</a>
        </div></div>'''

# --- VENDA E CARRINHO (MANTIDOS) ---
@app.route("/vender")
def vender():
    if "usuario" not in session: return redirect("/")
    prods = query_db("SELECT * FROM produtos")
    lista_html = ""
    for p in prods:
        botoes = "".join([f"<a href='/add/{p['codigo']}/{t}' style='padding:5px; background:white; border:1px solid #000; text-decoration:none; color:black; margin-right:5px;'>{t}({p[t]})</a>" if p[t]>0 else f"<span style='color:#ccc;'>{t}(0)</span> " for t in ["P","M","G","GG"]])
        lista_html += f"<div class='prod-item' data-info='{p['nome'].lower()}' style='border-bottom:1px solid #ddd; padding:10px;'><strong>{p['nome']}</strong> - R${p['preco']:.2f}<br>{botoes}</div>"
    carrinho = session.get("carrinho", [])
    total_c = sum(item['preco'] for item in carrinho)
    itens_html = "".join([f"<li>{i['nome']} ({i['tamanho']}) - R${i['preco']:.2f} <a href='/remover_item/{idx}'>[X]</a></li>" for idx, i in enumerate(carrinho)])
    return f'''<div style="font-family:sans-serif; display:flex; padding:20px; gap:20px; flex-wrap:wrap;">
        <div style="flex:2; min-width:300px;">
            <input id="busca" onkeyup="filtrar()" placeholder="Buscar..." style="width:100%; padding:10px; margin-bottom:15px;">
            <div style="max-height:400px; overflow-y:auto;">{lista_html}</div>
            <br><a href="/painel">⬅ Menu</a>
        </div>
        <div style="flex:1; min-width:250px; background:#f4f4f4; padding:20px; border-radius:10px; border:1px solid #ccc;">
            <h3>🛒 Carrinho</h3><ul>{itens_html}</ul><hr>
            <h4>Total: R$ {total_c:.2f}</h4>
            {"<a href='/checkout' style='background:green; color:white; padding:15px; display:block; text-align:center; text-decoration:none;'>FECHAR VENDA</a>" if carrinho else ""}
        </div></div>
        <script>function filtrar() {{ let v = document.getElementById('busca').value.toLowerCase(); let itens = document.getElementsByClassName('prod-item'); for(let i of itens) {{ i.style.display = i.getAttribute('data-info').includes(v) ? "" : "none"; }} }}</script>'''

@app.route("/add/<cod>/<tam>")
def add(cod, tam):
    p = query_db("SELECT * FROM produtos WHERE codigo=?", (cod,), one=True)
    if p and p[tam] > 0:
        conn = sqlite3.connect(DB_NAME); cur = conn.cursor()
        cur.execute(f"UPDATE produtos SET {tam} = {tam} - 1 WHERE codigo=?", (cod,))
        conn.commit(); conn.close()
        c = session.get("carrinho", [])
        c.append({"nome": p["nome"], "tamanho": tam, "preco": p["preco"], "cod": cod})
        session["carrinho"] = c
    return redirect("/vender")

@app.route("/remover_item/<int:index>")
def remover_item(index):
    c = session.get("carrinho", [])
    item = c.pop(index)
    conn = sqlite3.connect(DB_NAME); cur = conn.cursor()
    cur.execute(f"UPDATE produtos SET {item['tamanho']} = {item['tamanho']} + 1 WHERE codigo=?", (item['cod'],))
    conn.commit(); conn.close()
    session["carrinho"] = c
    return redirect("/vender")

@app.route("/checkout")
def checkout():
    total = sum(i['preco'] for i in session.get("carrinho", []))
    return f'''<div style="font-family:sans-serif; padding:20px; max-width:400px; margin:auto; border:1px solid #ccc; border-radius:10px;">
        <h2>Pagamento</h2>
        <h3>Total: R$ <span id="val">{total:.2f}</span></h3>
        <form method="post" action="/finalizar">
            <select name="pagamento" id="pag" onchange="calc({total})" style="width:100%; padding:10px;">
                <option value="Dinheiro">Dinheiro</option><option value="Pix">Pix</option>
                <option value="Cartão">Cartão (+14%)</option><option value="A prazo">A prazo</option>
            </select><br><br>
            <div id="c" style="display:none;">Nome Cliente:<br><input name="cliente" style="width:95%;"></div>
            <button style="width:100%; padding:15px; background:green; color:white; margin-top:10px;">CONFIRMAR</button>
        </form></div>
        <script>function calc(b) {{ let p = document.getElementById('pag').value; document.getElementById('val').innerText = (p=='Cartão'?(b*1.14):b).toFixed(2); document.getElementById('c').style.display = (p=='A prazo'?'block':'none'); }}</script>'''

@app.route("/finalizar", methods=["POST"])
def finalizar():
    c = session.get("carrinho", [])
    pag, cli = request.form["pagamento"], request.form.get("cliente", "Consumidor")
    total = sum(i['preco'] for i in c)
    if pag == "Cartão": total = round(total * 1.14, 2)
    conn = sqlite3.connect(DB_NAME); cur = conn.cursor()
    cur.execute("INSERT INTO vendas (data, total, pagamento, cliente, parcelas) VALUES (?,?,?,?,?)", (datetime.now().strftime("%d/%m/%Y %H:%M"), total, pag, cli, "1"))
    cur.execute("UPDATE caixa SET valor = valor + ? WHERE metodo = ?", (total, pag))
    conn.commit(); conn.close()
    session["carrinho"] = []
    return f"Venda Sucesso! <a href='/painel'>Voltar</a><script>window.print();</script>"

# --- ESTOQUE (COM EDITAR E EXCLUIR) ---
@app.route("/estoque")
def estoque():
    if session.get("nivel") != "total": return "Acesso negado"
    prods = query_db("SELECT * FROM produtos")
    tabela = ""
    for p in prods:
        tabela += f'''<tr>
            <td>{p['codigo']}</td>
            <td>{p['nome']}</td>
            <td>{p['P']}|{p['M']}|{p['G']}|{p['GG']}</td>
            <td>R$ {p['preco']:.2f}</td>
            <td>
                <a href="/editar_produto/{p['codigo']}" style="color: blue; text-decoration: none; margin-right: 10px;">[Editar]</a>
                <a href="/excluir_produto/{p['codigo']}" onclick="return confirm('Tem certeza?')" style="color: red; text-decoration: none;">[Excluir]</a>
            </td>
        </tr>'''
    return f'''<div style="font-family:sans-serif; padding:20px;">
        <h2>Cadastro de Estoque</h2>
        <form method="post" action="/cadastrar" style="background: #f9f9f9; padding: 15px; border-radius: 5px;">
            Cod: <input name="codigo" size="5" required> Nome: <input name="nome" required> Preço: <input name="preco" size="5" required> 
            P:<input name="P" size="2" value="0"> M:<input name="M" size="2" value="0"> G:<input name="G" size="2" value="0"> GG:<input name="GG" size="2" value="0">
            <button style="background: black; color: white; border: none; padding: 5px 15px; cursor: pointer;">Adicionar</button>
        </form><hr>
        <table border="1" style="width:100%; border-collapse: collapse; text-align: left;">
            <tr style="background: #eee;"><th>Cód</th><th>Nome</th><th>Grade</th><th>Preço</th><th>Ações</th></tr>
            {tabela}
        </table><br><a href="/painel">⬅ Voltar</a></div>'''

@app.route("/cadastrar", methods=["POST"])
def cadastrar():
    f = request.form
    conn = sqlite3.connect(DB_NAME); cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO produtos VALUES (?,?,?,?,?,?,?,?)", (f['codigo'], f['nome'], "", float(f['preco']), int(f['P']), int(f['M']), int(f['G']), int(f['GG'])))
    conn.commit(); conn.close()
    return redirect("/estoque")

@app.route("/editar_produto/<codigo>")
def editar_produto(codigo):
    p = query_db("SELECT * FROM produtos WHERE codigo=?", (codigo,), one=True)
    return f'''<div style="font-family:sans-serif; padding:20px;">
        <h2>Editar Produto: {p['nome']}</h2>
        <form method="post" action="/salvar_edicao">
            <input type="hidden" name="codigo" value="{p['codigo']}">
            Nome: <input name="nome" value="{p['nome']}"><br><br>
            Preço: <input name="preco" value="{p['preco']}"><br><br>
            P: <input name="P" value="{p['P']}"> M: <input name="M" value="{p['M']}"> 
            G: <input name="G" value="{p['G']}"> GG: <input name="GG" value="{p['GG']}"><br><br>
            <button style="padding: 10px 20px; background: blue; color: white; border: none;">Salvar Alterações</button>
            <a href="/estoque">Cancelar</a>
        </form></div>'''

@app.route("/salvar_edicao", methods=["POST"])
def salvar_edicao():
    f = request.form
    conn = sqlite3.connect(DB_NAME); cur = conn.cursor()
    cur.execute("UPDATE produtos SET nome=?, preco=?, P=?, M=?, G=?, GG=? WHERE codigo=?", (f['nome'], float(f['preco']), int(f['P']), int(f['M']), int(f['G']), int(f['GG']), f['codigo']))
    conn.commit(); conn.close()
    return redirect("/estoque")

@app.route("/excluir_produto/<codigo>")
def excluir_produto(codigo):
    conn = sqlite3.connect(DB_NAME); cur = conn.cursor()
    cur.execute("DELETE FROM produtos WHERE codigo=?", (codigo,))
    conn.commit(); conn.close()
    return redirect("/estoque")

# --- CAIXA E HISTÓRICO (MANTIDOS) ---
@app.route("/caixa")
def ver_caixa():
    dados = query_db("SELECT * FROM caixa")
    res = "".join([f"<p>{d['metodo']}: R$ {d['valor']:.2f}</p>" for d in dados])
    return f"<div style='padding:20px; font-family:sans-serif;'><h2>Resumo de Caixa</h2>{res}<a href='/painel'>Voltar</a></div>"

@app.route("/historico")
def historico():
    v = query_db("SELECT * ORDER BY id DESC") # Simplificado para exemplo
    v = query_db("SELECT * FROM vendas ORDER BY id DESC")
    lista = "".join([f"<li>{x['data']} - {x['cliente']} - R${x['total']:.2f} ({x['pagamento']})</li>" for x in v])
    return f"<div style='padding:20px; font-family:sans-serif;'><h2>Histórico de Vendas</h2><ul>{lista}</ul><a href='/painel'>Voltar</a></div>"

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)