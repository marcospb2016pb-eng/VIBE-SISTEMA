import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = "vibe_2026_key"

# Conexão robusta com o banco de dados
def get_db_connection():
    db_path = os.path.join(os.getcwd(), 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Inicialização do Banco com todos os campos necessários
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('user')
        password = request.form.get('password')
        if (user == 'admin' and password == 'admin123') or (user == 'vendedor' and password == 'vibe123'):
            session['user'] = user
            return redirect(url_for('menu'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

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
    produtos = conn.execute('SELECT * FROM produtos').fetchall()
    conn.close()
    return render_template('vendas_aba.html', produtos=produtos)

@app.route('/historico_aba')
def historico_aba():
    conn = get_db_connection()
    vendas = conn.execute('SELECT * FROM vendas ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('historico_aba.html', vendas=vendas)

# --- ROTAS DE OPERAÇÃO DE ESTOQUE ---

@app.route('/remover_estoque', methods=['POST'])
def remover_estoque():
    data = request.json
    conn = get_db_connection()
    conn.execute(f"UPDATE produtos SET {data['tam'].lower()} = {data['tam'].lower()} - 1 WHERE id = ?", (data['id'],))
    conn.commit()
    conn.close()
    return jsonify(status="ok")

@app.route('/devolver_estoque', methods=['POST'])
def devolver_estoque():
    data = request.json
    conn = get_db_connection()
    conn.execute(f"UPDATE produtos SET {data['tam'].lower()} = {data['tam'].lower()} + 1 WHERE id = ?", (data['id'],))
    conn.commit()
    conn.close()
    return jsonify(status="ok")

# --- ROTAS DE VENDA E IMPRESSÃO ---

@app.route('/finalizar_venda', methods=['POST'])
def finalizar_venda():
    data = request.json
    conn = get_db_connection()
    conn.execute('INSERT INTO vendas (detalhes, valor_pago, forma_pagamento) VALUES (?,?,?)',
                 (data['detalhes'], data['total'], data['metodo']))
    conn.commit()
    conn.close()
    return jsonify(status="ok")

@app.route('/gerar_cupom_print')
def gerar_cupom_print():
    """Rota que preenche o arquivo cupom.html para a impressora térmica"""
    itens = request.args.get('itens', '')
    total = request.args.get('total', '0.00')
    metodo = request.args.get('metodo', '')
    data_hora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    
    return render_template('cupom.html', itens=itens, total=total, metodo=metodo, data=data_hora)

@app.route('/cupom_vazia')
def cupom_vazia():
    """Página em branco inicial para o iframe de impressão"""
    return "<html><body></body></html>"

# --- ROTAS DE GESTÃO DE PRODUTOS ---

@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    f = request.form
    conn = get_db_connection()
    conn.execute('INSERT INTO produtos (codigo, nome, cor, preco, p, m, g, gg) VALUES (?,?,?,?,?,?,?,?)',
                 (f.get('codigo'), f.get('nome'), f.get('cor'), float(f.get('preco',0)), 
                  int(f.get('P',0)), int(f.get('M',0)), int(f.get('G',0)), int(f.get('GG',0))))
    conn.commit()
    conn.close()
    return redirect(url_for('estoque_aba'))

@app.route('/deletar/<int:id>')
def deletar(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM produtos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('estoque_aba'))

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    conn = get_db_connection()
    produto = conn.execute('SELECT * FROM produtos WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        f = request.form
        conn.execute('''UPDATE produtos SET codigo=?, nome=?, cor=?, preco=?, p=?, m=?, g=?, gg=? 
                        WHERE id=?''',
                     (f.get('codigo'), f.get('nome'), f.get('cor'), float(f.get('preco')), 
                      int(f.get('P')), int(f.get('M')), int(f.get('G')), int(f.get('GG')), id))
        conn.commit()
        conn.close()
        return redirect(url_for('estoque_aba'))
    
    conn.close()
    return render_template('editar_produto.html', p=produto)
    
# CONFIGURAÇÃO CRÍTICA PARA O RENDER
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
