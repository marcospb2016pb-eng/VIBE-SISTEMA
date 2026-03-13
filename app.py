import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Configuração do banco de dados
def get_db_connection():
    # O Render usa um sistema de arquivos efêmero; 
    # se o banco sumir, ele será recriado automaticamente.
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Criar a tabela caso não exista
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT,
            nome TEXT,
            preco REAL,
            p INTEGER,
            m INTEGER,
            g INTEGER,
            gg INTEGER
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
    
    # Pega os valores do formulário. 
    # Se o campo estiver vazio (''), ele define como 0 ou 0.0 automaticamente.
    codigo = f.get('codigo') or "S/C"
    nome = f.get('nome') or "SEM NOME"
    
    try:
        # A lógica abaixo evita o erro "ValueError: could not convert string to float"
        preco = float(f.get('preco')) if f.get('preco') else 0.0
        p = int(f.get('P')) if f.get('P') else 0
        m = int(f.get('M')) if f.get('M') else 0
        g = int(f.get('G')) if f.get('G') else 0
        gg = int(f.get('GG')) if f.get('GG') else 0
    except ValueError:
        preco, p, m, g, gg = 0.0, 0, 0, 0, 0

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO produtos (codigo, nome, preco, p, m, g, gg) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (codigo, nome, preco, p, m, g, gg)
    )
    conn.commit()
    conn.close()
    
    return redirect(url_for('estoque'))

# Rota para deletar (caso precise limpar algo errado)
@app.route('/deletar/<int:id>')
def deletar(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM produtos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('estoque'))

if __name__ == '__main__':
    # O Render exige que o host seja 0.0.0.0
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
