import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

def get_db_connection():
    db_path = os.path.join(os.getcwd(), 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT, nome TEXT, preco REAL,
        p INTEGER, m INTEGER, g INTEGER, gg INTEGER)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produto_id INTEGER, tamanho TEXT, quantidade INTEGER,
        valor_total REAL, data TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def menu():
    return render_template('menu.html')

@app.route('/estoque')
def estoque():
    conn = get_db_connection()
    produtos = conn.execute('SELECT * FROM produtos').fetchall()
    vendas = conn.execute('SELECT v.*, p.nome FROM vendas v JOIN produtos p ON v.produto_id = p.id ORDER BY v.id DESC LIMIT 10').fetchall()
    conn.close()
    return render_template('estoque.html', produtos=produtos, vendas=vendas, edit_item=None)

@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    f = request.form
    try:
        preco = float(f.get('preco')) if f.get('preco') else 0.0
        conn = get_db_connection()
        conn.execute('INSERT INTO produtos (codigo, nome, preco, p, m, g, gg) VALUES (?,?,?,?,?,?,?)',
                     (f.get('codigo'), f.get('nome'), preco, int(f.get('P',0)), int(f.get('M',0)), int(f.get('G',0)), int(f.get('GG',0))))
        conn.commit()
        conn.close()
    except: pass
    return redirect(url_for('estoque'))

@app.route('/pre-editar/<int:id>')
def pre_editar(id):
    conn = get_db_connection()
    produtos = conn.execute('SELECT * FROM produtos').fetchall()
    vendas = conn.execute('SELECT v.*, p.nome FROM vendas v JOIN produtos p ON v.produto_id = p.id ORDER BY v.id DESC LIMIT 5').fetchall()
    item = conn.execute('SELECT * FROM produtos WHERE id = ?', (id,)).fetchone()
    conn.close()
    return render_template('estoque.html', produtos=produtos, vendas=vendas, edit_item=item)

@app.route('/editar/<int:id>', methods=['POST'])
def editar(id):
    f = request.form
    conn = get_db_connection()
    conn.execute('UPDATE produtos SET codigo=?, nome=?, preco=?, p=?, m=?, g=?, gg=? WHERE id=?',
                 (f.get('codigo'), f.get('nome'), float(f.get('preco', 0)), 
                  int(f.get('P', 0)), int(f.get('M', 0)), int(f.get('G', 0)), int(f.get('GG', 0)), id))
    conn.commit()
    conn.close()
    return redirect(url_for('estoque'))

@app.route('/vender', methods=['POST'])
def vender():
    prod_id = request.form.get('produto_id')
    tamanho = request.form.get('tamanho').lower()
    qtd = int(request.form.get('qtd', 1))
    conn = get_db_connection()
    p = conn.execute('SELECT * FROM produtos WHERE id = ?', (prod_id,)).fetchone()
    if p and p[tamanho] >= qtd:
        conn.execute(f'UPDATE produtos SET {tamanho} = ? WHERE id = ?', (p[tamanho]-qtd, prod_id))
        conn.execute('INSERT INTO vendas (produto_id, tamanho, quantidade, valor_total) VALUES (?,?,?,?)',
                     (prod_id, tamanho.upper(), qtd, p['preco']*qtd))
        conn.commit()
    conn.close()
    return redirect(url_for('estoque'))

@app.route('/deletar/<int:id>')
def deletar(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM produtos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('estoque'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
