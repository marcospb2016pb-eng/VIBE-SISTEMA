import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

def get_db_connection():
    # Usando um caminho absoluto para evitar erros de permissão no Render
    db_path = os.path.join(os.getcwd(), 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT,
            nome TEXT,
            preco REAL,
            p INTEGER, m INTEGER, g INTEGER, gg INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return redirect(url_for('estoque'))

@app.route('/estoque')
def estoque():
    conn = get_db_connection()
    produtos = conn.execute('SELECT * FROM produtos').fetchall()
    conn.close()
    return render_template('estoque.html', produtos=produtos)

@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    f = request.form
    try:
        # Garante que campos vazios não quebrem o sistema
        preco = float(f.get('preco')) if f.get('preco') and f.get('preco').strip() else 0.0
        p = int(f.get('P')) if f.get('P') and f.get('P').strip() else 0
        m = int(f.get('M')) if f.get('M') and f.get('M').strip() else 0
        g = int(f.get('G')) if f.get('G') and f.get('G').strip() else 0
        gg = int(f.get('GG')) if f.get('GG') and f.get('GG').strip() else 0
        
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO produtos (codigo, nome, preco, p, m, g, gg) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (f.get('codigo', 'S/C'), f.get('nome', 'SEM NOME'), preco, p, m, g, gg)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erro ao cadastrar: {e}")
        
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
