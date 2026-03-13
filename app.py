import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "vibe_2026_key"

def get_db_connection():
    db_path = os.path.join(os.getcwd(), 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Banco de Dados atualizado com COR
def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT, nome TEXT, cor TEXT, preco REAL,
        p INTEGER, m INTEGER, g INTEGER, gg INTEGER)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        detalhes TEXT, valor_pago REAL, forma_pagamento TEXT, data TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def menu():
    if 'user' not in session: return render_template('login.html')
    return render_template('menu.html', user=session['user'])

@app.route('/login', methods=['POST'])
def login():
    user = request.form.get('user')
    password = request.form.get('password')
    if (user == 'admin' and password == 'admin123') or (user == 'vendedor' and password == 'vibe123'):
        session['user'] = user
        return redirect(url_for('menu'))
    return redirect(url_for('menu'))

@app.route('/estoque_aba')
def estoque_aba():
    if session.get('user') != 'admin': return "Acesso Negado", 403
    conn = get_db_connection()
    produtos = conn.execute('SELECT * FROM produtos').fetchall()
    conn.close()
    return render_template('estoque_aba.html', produtos=produtos)

@app.route('/vendas_aba')
def vendas_aba():
    conn = get_db_connection()
    produtos = conn.execute('SELECT * FROM produtos WHERE (p+m+g+gg) > 0').fetchall()
    conn.close()
    return render_template('vendas_aba.html', produtos=produtos)

@app.route('/finalizar_venda', methods=['POST'])
def finalizar_venda():
    data = request.json
    total = float(data['total'])
    metodo = data['metodo']
    itens = data['itens']
    
    if metodo == "Cartão": total *= 1.14 # +14% automático
    
    conn = get_db_connection()
    # Detalhes para o histórico e cupom
    detalhes = ", ".join([f"{i['nome']} ({i['tam']})" for i in itens])
    conn.execute('INSERT INTO vendas (detalhes, valor_pago, forma_pagamento) VALUES (?,?,?)',
                 (detalhes, total, metodo))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.route('/devolver_estoque', methods=['POST'])
def devolver_estoque():
    data = request.json
    conn = get_db_connection()
    conn.execute(f"UPDATE produtos SET {data['tam'].lower()} = {data['tam'].lower()} + 1 WHERE id = ?", (data['id'],))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.route('/remover_estoque', methods=['POST'])
def remover_estoque():
    data = request.json
    conn = get_db_connection()
    conn.execute(f"UPDATE produtos SET {data['tam'].lower()} = {data['tam'].lower()} - 1 WHERE id = ?", (data['id'],))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.route('/historico_aba')
def historico_aba():
    conn = get_db_connection()
    vendas = conn.execute('SELECT * FROM vendas ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('historico_aba.html', vendas=vendas)

# Rotas de Cadastro, Editar e Excluir permanecem as mesmas (omitidas por brevidade mas devem ser mantidas)
@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    f = request.form
    conn = get_db_connection()
    conn.execute('INSERT INTO produtos (codigo, nome, cor, preco, p, m, g, gg) VALUES (?,?,?,?,?,?,?,?)',
                 (f.get('codigo'), f.get('nome'), f.get('cor'), float(f.get('preco', 0)), int(f.get('P',0)), int(f.get('M',0)), int(f.get('G',0)), int(f.get('GG',0))))
    conn.commit()
    conn.close()
    return redirect(url_for('estoque_aba'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
