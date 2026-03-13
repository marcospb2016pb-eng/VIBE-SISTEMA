import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = "vibe_sistema_secret"

def get_db_connection():
    db_path = os.path.join(os.getcwd(), 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT, nome TEXT, preco REAL, p INTEGER, m INTEGER, g INTEGER, gg INTEGER)')
    conn.execute('CREATE TABLE IF NOT EXISTS vendas (id INTEGER PRIMARY KEY AUTOINCREMENT, produto_id INTEGER, tamanho TEXT, quantidade INTEGER, valor_pago REAL, forma_pagamento TEXT, parcelas INTEGER, data TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    user = request.form.get('user')
    password = request.form.get('password')
    if user == 'admin' and password == 'admin123':
        session['user'] = 'admin'
        return redirect(url_for('estoque'))
    elif user == 'vendedor' and password == 'vibe123':
        session['user'] = 'vendedor'
        return redirect(url_for('estoque'))
    else:
        flash('Login inválido!')
        return redirect(url_for('login_page'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/estoque')
def estoque():
    if 'user' not in session: return redirect(url_for('login_page'))
    conn = get_db_connection()
    produtos = conn.execute('SELECT * FROM produtos').fetchall()
    vendas = conn.execute('SELECT v.*, p.nome FROM vendas v JOIN produtos p ON v.produto_id = p.id ORDER BY v.id DESC LIMIT 10').fetchall()
    item_edit = None
    if request.args.get('edit_id'):
        item_edit = conn.execute('SELECT * FROM produtos WHERE id = ?', (request.args.get('edit_id'),)).fetchone()
    conn.close()
    return render_template('estoque.html', produtos=produtos, vendas=vendas, edit_item=item_edit, user=session['user'])

@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    if session.get('user') != 'admin': return "Acesso negado", 403
    f = request.form
    conn = get_db_connection()
    conn.execute('INSERT INTO produtos (codigo, nome, preco, p, m, g, gg) VALUES (?,?,?,?,?,?,?)',
                 (f.get('codigo'), f.get('nome'), float(f.get('preco', 0)), int(f.get('P',0)), int(f.get('M',0)), int(f.get('G',0)), int(f.get('GG',0))))
    conn.commit()
    conn.close()
    return redirect(url_for('estoque'))

@app.route('/vender', methods=['POST'])
def vender():
    f = request.form
    prod_id = f.get('produto_id')
    tamanho = f.get('tamanho').lower()
    qtd = int(f.get('qtd', 1))
    pagamento = f.get('pagamento')
    parcelas = int(f.get('parcelas', 1))
    
    conn = get_db_connection()
    p = conn.execute('SELECT * FROM produtos WHERE id = ?', (prod_id,)).fetchone()
    
    if p and p[tamanho] >= qtd:
        valor_base = p['preco'] * qtd
        # Regra do Cartão: +14%
        valor_final = valor_base * 1.14 if pagamento == 'Cartão' else valor_base
        
        conn.execute(f'UPDATE produtos SET {tamanho} = ? WHERE id = ?', (p[tamanho]-qtd, prod_id))
        conn.execute('INSERT INTO vendas (produto_id, tamanho, quantidade, valor_pago, forma_pagamento, parcelas) VALUES (?,?,?,?,?,?)',
                     (prod_id, tamanho.upper(), qtd, valor_final, pagamento, parcelas))
        conn.commit()
    conn.close()
    return redirect(url_for('estoque'))

@app.route('/editar/<int:id>', methods=['POST'])
def editar(id):
    f = request.form
    conn = get_db_connection()
    conn.execute('UPDATE produtos SET codigo=?, nome=?, preco=?, p=?, m=?, g=?, gg=? WHERE id=?',
                 (f.get('codigo'), f.get('nome'), float(f.get('preco', 0)), int(f.get('P', 0)), int(f.get('M', 0)), int(f.get('G', 0)), int(f.get('GG', 0)), id))
    conn.commit()
    conn.close()
    return redirect(url_for('estoque'))

@app.route('/imprimir/<int:venda_id>')
def imprimir(venda_id):
    conn = get_db_connection()
    venda = conn.execute('SELECT v.*, p.nome, p.codigo FROM vendas v JOIN produtos p ON v.produto_id = p.id WHERE v.id = ?', (venda_id,)).fetchone()
    conn.close()
    return render_template('cupom.html', v=venda)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
