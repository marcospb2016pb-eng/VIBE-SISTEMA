import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = "vibe_2026_key"

# Conexão com o Supabase (PostgreSQL) usando a variável de ambiente do Render
def get_db_connection():
    # O Render vai ler o link com a senha que você configurou em 'Environment'
    url = os.environ.get("DATABASE_URL")
    conn = psycopg2.connect(url)
    return conn

# Inicialização das tabelas no Supabase (não apagam mais)
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # No PostgreSQL, usamos SERIAL em vez de AUTOINCREMENT
    cur.execute('''CREATE TABLE IF NOT EXISTS produtos (
        id SERIAL PRIMARY KEY,
        codigo TEXT, nome TEXT, cor TEXT, preco REAL,
        p INTEGER, m INTEGER, g INTEGER, gg INTEGER)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS vendas (
        id SERIAL PRIMARY KEY,
        detalhes TEXT, valor_pago REAL, forma_pagamento TEXT, data TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    cur.close()
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
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM produtos ORDER BY id DESC')
    produtos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('estoque_aba.html', produtos=produtos)

@app.route('/vendas_aba')
def vendas_aba():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM produtos ORDER BY nome ASC')
    produtos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('vendas_aba.html', produtos=produtos)

@app.route('/historico_aba')
def historico_aba():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM vendas ORDER BY id DESC')
    vendas = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('historico_aba.html', vendas=vendas)

@app.route('/remover_estoque', methods=['POST'])
def remover_estoque():
    data = request.json
    coluna = data['tam'].lower()
    conn = get_db_connection()
    cur = conn.cursor()
    # No PostgreSQL usamos %s no lugar de ?
    cur.execute(f"UPDATE produtos SET {coluna} = {coluna} - 1 WHERE id = %s", (data['id'],))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify(status="ok")

@app.route('/devolver_estoque', methods=['POST'])
def devolver_estoque():
    data = request.json
    coluna = data['tam'].lower()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"UPDATE produtos SET {coluna} = {coluna} + 1 WHERE id = %s", (data['id'],))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify(status="ok")

@app.route('/finalizar_venda', methods=['POST'])
def finalizar_venda():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO vendas (detalhes, valor_pago, forma_pagamento) VALUES (%s,%s,%s)',
                 (data['detalhes'], data['total'], data['metodo']))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify(status="ok")

@app.route('/gerar_cupom_print')
def gerar_cupom_print():
    itens = request.args.get('itens', '')
    total = request.args.get('total', '0.00')
    metodo = request.args.get('metodo', '')
    data_hora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    return render_template('cupom.html', itens=itens, total=total, metodo=metodo, data=data_hora)

@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    f = request.form
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO produtos (codigo, nome, cor, preco, p, m, g, gg) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
                 (f.get('codigo'), f.get('nome'), f.get('cor'), float(f.get('preco',0)), 
                  int(f.get('P',0)), int(f.get('M',0)), int(f.get('G',0)), int(f.get('GG',0))))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('estoque_aba'))

@app.route('/deletar/<int:id>')
def deletar(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM produtos WHERE id = %s', (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('estoque_aba'))

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    if request.method == 'POST':
        f = request.form
        cur.execute('''UPDATE produtos SET codigo=%s, nome=%s, cor=%s, preco=%s, p=%s, m=%s, g=%s, gg=%s 
                        WHERE id=%s''',
                     (f.get('codigo'), f.get('nome'), f.get('cor'), float(f.get('preco')), 
                      int(f.get('P')), int(f.get('M')), int(f.get('G')), int(f.get('GG')), id))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('estoque_aba'))
    
    cur.execute('SELECT * FROM produtos WHERE id = %s', (id,))
    produto = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('editar_produto.html', p=produto)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
